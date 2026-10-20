"""
Undo/Redo command manager for document edits and markups.
"""

from typing import List, Callable, Any, Optional

class ActionCommand:
    def __init__(self, description: str, undo_fn: Callable[[], Any], redo_fn: Callable[[], Any]):
        self.description = description
        self.undo_fn = undo_fn
        self.redo_fn = redo_fn

    def undo(self):
        self.undo_fn()

    def redo(self):
        self.redo_fn()

class HistoryManager:
    """Manages document undo/redo state stacks and tracks document modification status."""
    def __init__(self, max_history: int = 50, on_changed: Optional[Callable[[bool], Any]] = None):
        self.max_history = max_history
        self._undo_stack: List[ActionCommand] = []
        self._redo_stack: List[ActionCommand] = []
        self._save_checkpoint: int = 0
        self._save_checkpoint_valid: bool = True
        self.on_changed: Optional[Callable[[bool], Any]] = on_changed

    @property
    def is_modified(self) -> bool:
        """Returns True if the document has changes relative to the last save point."""
        if not self._save_checkpoint_valid:
            return True
        return len(self._undo_stack) != self._save_checkpoint

    def mark_saved(self):
        """Sets the current stack position as the clean saved state."""
        self._save_checkpoint = len(self._undo_stack)
        self._save_checkpoint_valid = True
        self._notify()

    def _notify(self):
        if self.on_changed:
            try:
                self.on_changed(self.is_modified)
            except Exception:
                pass

    def push(self, command: ActionCommand):
        self._undo_stack.append(command)
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
            if self._save_checkpoint > 0:
                self._save_checkpoint -= 1
            else:
                self._save_checkpoint_valid = False
        self._redo_stack.clear()
        self._notify()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        self._notify()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.redo()
        self._undo_stack.append(cmd)
        self._notify()
        return True

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._save_checkpoint = 0
        self._save_checkpoint_valid = True
        self._notify()

