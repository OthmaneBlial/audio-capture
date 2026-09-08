//! Bounded transcript state with deterministic ordering and review actions.

use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

const MAX_UNDO_ENTRIES: usize = 100;
const MAX_UNDO_CHARS: usize = 500_000;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SegmentStatus {
    Pending,
    Transcribing,
    Complete,
    Error,
    Cancelled,
}

impl SegmentStatus {
    pub fn label(self) -> &'static str {
        match self {
            Self::Pending => "Pending",
            Self::Transcribing => "Transcribing",
            Self::Complete => "Complete",
            Self::Error => "Error",
            Self::Cancelled => "Cancelled",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Segment {
    pub sequence: u64,
    pub status: SegmentStatus,
    pub text: String,
    pub detail: Option<String>,
}

#[derive(Debug, Clone, Default)]
pub struct Transcript {
    text: String,
    segments: Vec<Segment>,
    undo: UndoHistory,
}

impl Transcript {
    pub fn text(&self) -> &str {
        &self.text
    }

    pub fn segments(&self) -> &[Segment] {
        &self.segments
    }

    pub fn set_text(&mut self, text: impl Into<String>) {
        let text = text.into();
        if text != self.text {
            self.undo.record(&self.text);
            self.text = text;
        }
    }

    pub fn update_segment(
        &mut self,
        sequence: u64,
        status: SegmentStatus,
        text: impl Into<String>,
        detail: Option<String>,
    ) {
        let text = text.into();
        if let Some(segment) = self
            .segments
            .iter_mut()
            .find(|item| item.sequence == sequence)
        {
            segment.status = status;
            segment.text = text;
            segment.detail = detail;
        } else {
            self.segments.push(Segment {
                sequence,
                status,
                text,
                detail,
            });
            self.segments.sort_by_key(|item| item.sequence);
        }
        self.rebuild_text_from_completed();
    }

    pub fn clear(&mut self) {
        self.text.clear();
        self.segments.clear();
        self.undo.clear();
    }

    pub fn undo(&mut self) -> bool {
        if let Some(previous) = self.undo.undo(&self.text) {
            self.text = previous;
            return true;
        }
        false
    }

    pub fn redo(&mut self) -> bool {
        if let Some(next) = self.undo.redo(&self.text) {
            self.text = next;
            return true;
        }
        false
    }

    fn rebuild_text_from_completed(&mut self) {
        let combined = self
            .segments
            .iter()
            .filter(|segment| {
                segment.status == SegmentStatus::Complete && !segment.text.trim().is_empty()
            })
            .map(|segment| segment.text.trim())
            .collect::<Vec<_>>()
            .join(" ");
        if combined != self.text {
            self.undo.record(&self.text);
            self.text = combined;
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct UndoHistory {
    undo: VecDeque<String>,
    redo: VecDeque<String>,
    chars: usize,
}

impl UndoHistory {
    pub fn record(&mut self, snapshot: &str) {
        if snapshot.is_empty() || snapshot.len() > MAX_UNDO_CHARS {
            self.redo.clear();
            return;
        }
        self.undo.push_back(snapshot.to_owned());
        self.chars += snapshot.len();
        while self.undo.len() > MAX_UNDO_ENTRIES || self.chars > MAX_UNDO_CHARS {
            if let Some(oldest) = self.undo.pop_front() {
                self.chars = self.chars.saturating_sub(oldest.len());
            }
        }
        self.redo.clear();
    }

    fn undo(&mut self, current: &str) -> Option<String> {
        let previous = self.undo.pop_back()?;
        self.chars = self.chars.saturating_sub(previous.len());
        if !current.is_empty() {
            self.redo.push_back(current.to_owned());
        }
        Some(previous)
    }

    fn redo(&mut self, current: &str) -> Option<String> {
        let next = self.redo.pop_back()?;
        if !current.is_empty() {
            self.undo.push_back(current.to_owned());
            self.chars += current.len();
        }
        Some(next)
    }

    pub fn clear(&mut self) {
        self.undo.clear();
        self.redo.clear();
        self.chars = 0;
    }

    pub fn retained_entries(&self) -> usize {
        self.undo.len() + self.redo.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn out_of_order_provider_events_render_in_sequence_order() {
        let mut transcript = Transcript::default();
        transcript.update_segment(2, SegmentStatus::Complete, "second", None);
        transcript.update_segment(1, SegmentStatus::Complete, "first", None);
        assert_eq!(transcript.text(), "first second");
        assert_eq!(transcript.segments()[0].sequence, 1);
    }

    #[test]
    fn clear_discards_review_history() {
        let mut transcript = Transcript::default();
        transcript.set_text("draft");
        transcript.clear();
        assert!(!transcript.undo());
        assert!(transcript.text().is_empty());
    }

    #[test]
    fn undo_history_stays_bounded() {
        let mut history = UndoHistory::default();
        for index in 0..10_000 {
            history.record(&format!("snapshot-{index}"));
        }
        assert!(history.retained_entries() <= MAX_UNDO_ENTRIES);
    }
}
