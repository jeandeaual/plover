from PyQt5.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
)
from PyQt5.QtGui import (
    QFont,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PyQt5.QtWidgets import (
    QListView,
    QStyle,
    QStyledItemDelegate,
)

from plover import _
from plover.translation import escape_translation


# i18n: Widget: “SuggestionsWidget”.
NO_SUGGESTIONS_STRING = _('no suggestions')
MAX_SUGGESTIONS_COUNT = 10


class SuggestionsDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._doc = QTextDocument()
        self._translation_char_format = QTextCharFormat()
        self._strokes_char_format = QTextCharFormat()
        self._strokes_char_format.font().setStyleHint(QFont.Monospace)

    @property
    def text_font(self):
        return self._translation_char_format.font()

    @text_font.setter
    def text_font(self, font):
        self._translation_char_format.setFont(font)

    @property
    def strokes_font(self):
        return self._strokes_char_format.font()

    @strokes_font.setter
    def strokes_font(self, font):
        self._strokes_char_format.setFont(font)

    def _format_suggestion(self, index):
        suggestion = index.data(Qt.DisplayRole)
        self._doc.clear()
        cursor = QTextCursor(self._doc)
        cursor.setCharFormat(self._translation_char_format)
        cursor.insertText(escape_translation(suggestion.text) + ':')
        if not suggestion.steno_list:
            cursor.insertText(' ' + NO_SUGGESTIONS_STRING)
            return
        for strokes_list in suggestion.steno_list[:MAX_SUGGESTIONS_COUNT]:
            cursor.insertBlock()
            cursor.setCharFormat(self._strokes_char_format)
            cursor.insertText('   ' + '/'.join(strokes_list))

    def paint(self, painter, option, index):
        painter.save()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.highlightedText()
        else:
            text_color = option.palette.text()
        self._translation_char_format.setForeground(text_color)
        self._strokes_char_format.setForeground(text_color)
        painter.translate(option.rect.topLeft())
        self._format_suggestion(index)
        self._doc.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        self._format_suggestion(index)
        return self._doc.size().toSize()


class SuggestionsModel(QAbstractListModel):

    def __init__(self):
        super().__init__()
        self._suggestion_list = []

    def rowCount(self, parent):
        return 0 if parent.isValid() else len(self._suggestion_list)

    def data(self, index, role):
        if not index.isValid():
            return None
        suggestion = self._suggestion_list[index.row()]
        if role == Qt.DisplayRole:
            return suggestion
        if role == Qt.AccessibleTextRole:
            translation = escape_translation(suggestion.text)
            if suggestion.steno_list:
                steno = ', '.join('/'.join(strokes_list) for strokes_list in
                                  suggestion.steno_list[:MAX_SUGGESTIONS_COUNT])
            else:
                steno = NO_SUGGESTIONS_STRING
            return translation + ': ' + steno
        return None

    def clear(self):
        self.modelAboutToBeReset.emit()
        self._suggestion_list.clear()
        self.modelReset.emit()

    def extend(self, suggestion_list):
        row = len(self._suggestion_list)
        self.beginInsertRows(QModelIndex(), row, row + len(suggestion_list))
        self._suggestion_list.extend(suggestion_list)
        self.endInsertRows()


class SuggestionsWidget(QListView):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setResizeMode(self.Adjust)
        self._model = SuggestionsModel()
        self._delegate = SuggestionsDelegate(self)
        self.setModel(self._model)
        self.setItemDelegate(self._delegate)

    def append(self, suggestion_list):
        scrollbar = self.verticalScrollBar()
        scroll_at_end = scrollbar.value() == scrollbar.maximum()
        self._model.extend(suggestion_list)
        if scroll_at_end:
            self.scrollToBottom()

    def clear(self):
        self._model.clear()

    def _reformat(self):
        self._model.layoutAboutToBeChanged.emit()
        self._model.layoutChanged.emit()

    @property
    def text_font(self):
        return self._delegate.text_font

    @text_font.setter
    def text_font(self, font):
        self._delegate.text_font = font
        self._reformat()

    @property
    def strokes_font(self):
        return self._delegate.strokes_font

    @strokes_font.setter
    def strokes_font(self, font):
        self._delegate.strokes_font = font
        self._reformat()
