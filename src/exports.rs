//! Explicit, atomic transcript exports.

use chrono::Utc;
use std::fs;
use std::io::Write;
use std::path::Path;
use tempfile::NamedTempFile;
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExportFormat {
    Text,
    Markdown,
    Timestamped,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExportDocument {
    pub extension: &'static str,
    pub suggested_name: String,
    pub contents: String,
}

#[derive(Debug, Error)]
pub enum ExportError {
    #[error("unsupported export format")]
    UnsupportedFormat,
    #[error("export destination is a symbolic link")]
    SymlinkDestination,
    #[error("could not write export: {0}")]
    Io(#[from] std::io::Error),
}

pub fn build_export(text: &str, format: ExportFormat) -> Result<ExportDocument, ExportError> {
    let clean = text.trim();
    if clean.is_empty() {
        return Ok(ExportDocument {
            extension: "txt",
            suggested_name: "transcript.txt".into(),
            contents: String::new(),
        });
    }
    match format {
        ExportFormat::Text => Ok(ExportDocument {
            extension: "txt",
            suggested_name: "transcript.txt".into(),
            contents: format!("{clean}\n"),
        }),
        ExportFormat::Markdown => Ok(ExportDocument {
            extension: "md",
            suggested_name: "transcript.md".into(),
            contents: format!("# Transcript\n\n{clean}\n"),
        }),
        ExportFormat::Timestamped => Ok(ExportDocument {
            extension: "txt",
            suggested_name: format!("transcript_{}.txt", Utc::now().format("%Y%m%d_%H%M%S")),
            contents: format!(
                "Voice Transcriber — {}\n\n{clean}\n",
                Utc::now().to_rfc3339()
            ),
        }),
    }
}

pub fn write_export(destination: &Path, document: &ExportDocument) -> Result<(), ExportError> {
    if destination.is_symlink() {
        return Err(ExportError::SymlinkDestination);
    }
    let parent = destination.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent)?;
    let mut temporary = NamedTempFile::new_in(parent)?;
    temporary.write_all(document.contents.as_bytes())?;
    temporary.as_file().sync_all()?;
    temporary
        .persist(destination)
        .map_err(|error| ExportError::Io(error.error))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn formats_are_explicit() {
        let markdown = build_export("Hello world", ExportFormat::Markdown).unwrap();
        assert_eq!(markdown.extension, "md");
        assert!(markdown.contents.starts_with("# Transcript"));
        let text = build_export("Hello world", ExportFormat::Text).unwrap();
        assert_eq!(text.contents, "Hello world\n");
    }

    #[cfg(unix)]
    #[test]
    fn symlink_destination_is_refused() {
        use std::os::unix::fs::symlink;
        let temporary = tempfile::tempdir().unwrap();
        let target = temporary.path().join("target.txt");
        let link = temporary.path().join("link.txt");
        fs::write(&target, "original").unwrap();
        symlink(&target, &link).unwrap();
        let document = build_export("secret", ExportFormat::Text).unwrap();
        assert!(matches!(
            write_export(&link, &document),
            Err(ExportError::SymlinkDestination)
        ));
        assert_eq!(fs::read_to_string(target).unwrap(), "original");
    }
}
