# Flatpak linter exception

The Flatpak ID `io.github.othmaneblial.audio_capture` shipped before the
Flathub linter gate was added. Flathub derives the affiliation URL
`https://github.com/othmaneblial/audio_capture` from that ID, while the
canonical repository uses the hyphenated name
`https://github.com/OthmaneBlial/audio-capture`.

Changing the application ID now would create a different installed application
and strand existing user data. CI therefore supplies one local exception:
`appid-url-not-reachable`. The actual homepage, bug tracker, VCS URL, release
source mapping, and immutable screenshot URLs remain explicit in AppStream.

No permission, filesystem, network, sandbox, source, AppStream-content, or
exported-repository error is excepted. A future Flathub submission must request
manual affiliation review or deliberately migrate the application ID; this
local CI exception is not represented as Flathub approval.
