
# coding: utf-8

from PyQt4.QtGui import QTreeWidgetItem, QListWidgetItem, QBrush, QColor, QIcon, QMovie


def create_list_resource_element(name, url=''):
    item = ListResourceTreeItem()
    item.setName(name)
    item.setUrl(url)

    return item

def create_operation_list_item(oper):
    item = SupportedOperationListItem(oper)
    return item

def create_property_list_item(prop):
    item = SupportedPropertyListItem(prop)
    return item

def create_icon(dir_=None):
    return QIcon(dir_)

def create_gif_icon(dir_=None):
    icon = QIcon()
    movie = QMovie(dir_)

    def update_icon():
        i = QIcon(movie.currentPixmap())
        icon.swap(i)

    movie.frameChanged.connect(update_icon)
    movie.start()

    return icon



# Classe de itens que serão adicionados à list_resource em dialog_construct_url_2
class ListResourceTreeItem(QTreeWidgetItem):
    # 0 - name
    # 1 - url
    def __init__(self):
        super(ListResourceTreeItem, self).__init__()

    def setName(self, name):
        self.setText(0, name)

    def name(self):
        return self.text(0)

    def setUrl(self, url):
        self.setText(1, url)
        self.setToolTip(0, url)

    def url(self):
        return self.text(1)


# Classe de itens que serão adicionados à list_attributes em dialog_construct_url_2
class SupportedOperationListItem(QListWidgetItem):
    def __init__(self, oper):
        from IBGEVisualizer.HyperResource import SupportedOperation

        if not isinstance(oper, SupportedOperation):
            return

        super(SupportedOperationListItem, self).__init__()

        self.property = oper
        self.type_ = 'supported_operation'
        self.name = self.property.name

        self.setText(self.name)

        self.setToolTip(str(self.property))
        self.setBackground(QBrush(QColor(255, 252, 226)))


class SupportedPropertyListItem(QListWidgetItem):
    def __init__(self, prop):
        from IBGEVisualizer.HyperResource import SupportedProperty

        if not isinstance(prop, SupportedProperty):
            return

        super(SupportedPropertyListItem, self).__init__()

        self.property = prop
        self.type_ = 'supported_property'
        self.name = self.property.name

        self.setText(self.name)

        self.setToolTip(str(self.property))
        self.setBackground(QBrush(QColor(255, 237, 248)))
