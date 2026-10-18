"""
Undo/Redo command manager for document edits and markups.
"""

from typing import List, Callable, Any

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
    """Manages document undo/redo state stacks."""
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._undo_stack: List[ActionCommand] = []
        self._redo_stack: List[ActionCommand] = []

    def push(self, command: ActionCommand):
        self._undo_stack.append(command)
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.redo()
        self._undo_stack.append(cmd)
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
