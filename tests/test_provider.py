import os
import stat
import tempfile
import unittest
from pathlib import Path

from transcription.groq_service import GroqTranscriptionService
from transcription.local_whisper import LocalWhisperTranscriptionService, local_mode_enabled
from transcription.provider import ProviderError


class FakeProcess:
    def __init__(self, command, **kwargs):
        self.command = command
        self.kwargs = kwargs
        self.returncode = 0
        self.terminated = False
        self.wav_data = b""

    def communicate(self, timeout=None):
        del timeout
        descriptor = self.kwargs["pass_fds"][0]
        os.lseek(descriptor, 0, os.SEEK_SET)
        self.wav_data = os.read(descriptor, 1_000_000)
        return " local words \n", ""

    def terminate(self):
        self.terminated = True


class FakeProcessFactory:
    def __init__(self):
        self.processes = []

    def __call__(self, command, **kwargs):
        process = FakeProcess(command, **kwargs)
        self.processes.append(process)
        return process


def failing_process_factory(_command, **_kwargs):
    raise OSError("synthetic local process failure")


class ProviderContractTests(unittest.TestCase):
    def test_groq_declares_capabilities_boundary_and_normalized_codes(self):
        service = GroqTranscriptionService(api_key="")
        try:
            self.assertEqual(service.provider_id, "groq")
            self.assertTrue(service.capabilities.translation_to_english)
            self.assertIn("fr", service.capabilities.supported_languages)
            self.assertIn("Completed speech segment", service.boundary.audio_destination)
            self.assertEqual(service.cancel_pending(), 0)
        finally:
            service.close(wait=True)

    def test_local_mode_requires_explicit_flag_and_is_disabled_in_flatpak(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            self.assertFalse(local_mode_enabled({}, flatpak_info=missing))
            self.assertTrue(
                local_mode_enabled(
                    {"VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL": "1"}, flatpak_info=missing
                )
            )
            flatpak_info = Path(directory) / ".flatpak-info"
            flatpak_info.touch()
            self.assertFalse(
                local_mode_enabled(
                    {"VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL": "1"},
                    flatpak_info=flatpak_info,
                )
            )

    def test_local_provider_uses_memory_descriptor_and_reports_states(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "whisper-cli"
            binary.write_text("placeholder")
            binary.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            model = Path(directory) / "ggml-tiny.bin"
            model.write_bytes(b"model")
            process_factory = FakeProcessFactory()
            descriptors = []

            def memfd_factory(_name, _flags):
                temporary = tempfile.TemporaryFile()
                descriptors.append(temporary)
                return os.dup(temporary.fileno())

            states = []
            received = []
            service = LocalWhisperTranscriptionService(
                binary_path=str(binary),
                model_path=str(model),
                language="fr",
                translate=True,
                process_factory=process_factory,
                memfd_factory=memfd_factory,
                environ={"VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL": "1"},
                flatpak_info=Path(directory) / "missing-flatpak-info",
                on_transcription=received.append,
                on_request_state=lambda *values: states.append(values),
            )
            try:
                future = service.transcribe_async(b"\x00\x00" * 160)
                assert future is not None
                self.assertEqual(future.result(timeout=2), "local words")
                for _ in range(100):
                    if any(state == "complete" for _, state, _ in states):
                        break
                    import time

                    time.sleep(0.001)
                self.assertEqual(received, ["local words"])
                self.assertEqual([state for _, state, _ in states], ["pending", "complete"])
                process = process_factory.processes[0]
                self.assertTrue(process.wav_data.startswith(b"RIFF"))
                self.assertIn("--translate", process.command)
                self.assertEqual(process.command[process.command.index("--language") + 1], "fr")
                self.assertIn("/proc/self/fd/", process.command[process.command.index("--file") + 1])
                self.assertIsNotNone(service.last_latency_ms)
            finally:
                service.close(wait=True)
                for descriptor in descriptors:
                    descriptor.close()

    def test_local_async_errors_keep_the_request_id(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "whisper-cli"
            binary.write_text("placeholder")
            binary.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            model = Path(directory) / "ggml-tiny.bin"
            model.write_bytes(b"model")
            descriptors = []

            def memfd_factory(_name, _flags):
                temporary = tempfile.TemporaryFile()
                descriptors.append(temporary)
                return os.dup(temporary.fileno())

            errors = []
            service = LocalWhisperTranscriptionService(
                binary_path=str(binary),
                model_path=str(model),
                process_factory=failing_process_factory,
                memfd_factory=memfd_factory,
                environ={"VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL": "1"},
                flatpak_info=Path(directory) / "missing-flatpak-info",
                on_error_result=lambda request_id, error: errors.append((request_id, error)),
            )
            try:
                future = service.transcribe_async(b"\x00\x00" * 80)
                assert future is not None
                with self.assertRaises(OSError):
                    future.result(timeout=2)
                for _ in range(100):
                    if errors:
                        break
                    import time

                    time.sleep(0.001)
                self.assertEqual(len(errors), 1)
                self.assertTrue(errors[0][0].startswith("local-segment-"))
                self.assertEqual(errors[0][1].code, "local_unexpected")
            finally:
                service.close(wait=True)
                for descriptor in descriptors:
                    descriptor.close()

    def test_local_process_created_during_close_is_terminated_before_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "whisper-cli"
            binary.write_text("placeholder")
            binary.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            model = Path(directory) / "ggml-tiny.bin"
            model.write_bytes(b"model")
            descriptors = []
            processes = []
            holder = {}

            def memfd_factory(_name, _flags):
                temporary = tempfile.TemporaryFile()
                descriptors.append(temporary)
                return os.dup(temporary.fileno())

            def closing_process_factory(command, **kwargs):
                holder["service"].close(wait=False)
                process = FakeProcess(command, **kwargs)
                processes.append(process)
                return process

            service = LocalWhisperTranscriptionService(
                binary_path=str(binary),
                model_path=str(model),
                process_factory=closing_process_factory,
                memfd_factory=memfd_factory,
                environ={"VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL": "1"},
                flatpak_info=Path(directory) / "missing-flatpak-info",
            )
            holder["service"] = service
            try:
                with self.assertRaises(ProviderError) as raised:
                    service._run_cli(b"RIFF-fake-wav")
                self.assertEqual(raised.exception.code, "shutdown")
                self.assertEqual(len(processes), 1)
                self.assertTrue(processes[0].terminated)
                self.assertEqual(service._processes, set())
            finally:
                service.close(wait=True)
                for descriptor in descriptors:
                    descriptor.close()


if __name__ == "__main__":
    unittest.main()
