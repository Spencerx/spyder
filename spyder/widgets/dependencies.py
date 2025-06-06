# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Module checking Spyder runtime dependencies"""

# Standard library imports
import sys

# Third party imports
from qtpy.QtGui import QColor
from qtpy.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
                            QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
                            QStackedWidget, QTreeWidget, QTreeWidgetItem)

# Local imports
from spyder import __version__
from spyder.api.widgets.dialogs import SpyderDialogButtonBox
from spyder.config.base import _
from spyder.config.gui import is_dark_interface
from spyder.dependencies import OPTIONAL, PLUGIN
from spyder.utils.icon_manager import ima
from spyder.utils.palette import SpyderPalette
from spyder.utils.stylesheet import AppStyle, MAC, WIN
from spyder.widgets.emptymessage import EmptyMessageWidget


class DependenciesTreeWidget(QTreeWidget):

    def update_dependencies(self, dependencies):
        self.clear()
        headers = (_("Module"), _("Package name"), _(" Required "),
                   _(" Installed "), _("Provided features"))
        self.setHeaderLabels(headers)

        # Mandatory items
        mandatory_item = QTreeWidgetItem([_("Mandatory")])
        font = mandatory_item.font(0)
        font.setBold(True)
        mandatory_item.setFont(0, font)

        # Optional items
        optional_item = QTreeWidgetItem([_("Optional")])
        optional_item.setFont(0, font)

        # Spyder plugins
        spyder_plugins = QTreeWidgetItem([_("Spyder plugins")])
        spyder_plugins.setFont(0, font)

        self.addTopLevelItems([mandatory_item, optional_item, spyder_plugins])

        for dependency in sorted(dependencies,
                                 key=lambda x: x.modname.lower()):
            item = QTreeWidgetItem([dependency.modname,
                                    dependency.package_name,
                                    dependency.required_version,
                                    dependency.installed_version,
                                    dependency.features])

            # Format content
            if dependency.check():
                item.setIcon(0, ima.icon('dependency_ok'))
            elif dependency.kind == OPTIONAL:
                item.setIcon(0, ima.icon('dependency_warning'))
                item.setBackground(2, QColor(SpyderPalette.COLOR_WARN_1))

                # Fix foreground color in the light theme
                if not is_dark_interface():
                    item.setForeground(
                        2, QColor(SpyderPalette.COLOR_BACKGROUND_1)
                    )
            else:
                item.setIcon(0, ima.icon('dependency_error'))
                item.setBackground(2, QColor(SpyderPalette.COLOR_ERROR_1))

                # Fix foreground color in the light theme
                if not is_dark_interface():
                    item.setForeground(
                        2, QColor(SpyderPalette.COLOR_BACKGROUND_1)
                    )

            # Add to tree
            if dependency.kind == OPTIONAL:
                optional_item.addChild(item)
            elif dependency.kind == PLUGIN:
                spyder_plugins.addChild(item)
            else:
                mandatory_item.addChild(item)

        self.expandAll()

    def resize_columns_to_contents(self):
        for col in range(self.columnCount()):
            self.resizeColumnToContents(col)


class DependenciesDialog(QDialog):

    def __init__(self, parent):
        QDialog.__init__(self, parent)

        # Widgets
        note1 = _(
            "Optional modules are not required to run Spyder but enhance "
            "its functions."
        )

        note2 = _(
            "New dependencies or changed ones will be correctly detected only "
            "after Spyder is restarted."
        )

        notes_vmargin = "0.4em" if WIN else "0.3em"
        label = QLabel(
            (
                "<style>"
                "ul, li {{margin-left: -15px}}"
                "li {{margin-bottom: {}}}"
                "</style>"
                "<ul>"
                "<li>{}</li>"
                "<li>{}</li>"
                "</ul>"
            ).format(notes_vmargin, note1, note2)
        )

        self.treewidget = DependenciesTreeWidget(self)
        self.copy_btn = QPushButton(_("Copy to clipboard"))
        ok_btn = SpyderDialogButtonBox(QDialogButtonBox.Ok)

        # Widget setup
        self.setWindowTitle(
            _("Dependencies for Spyder {}").format(__version__)
        )
        self.setModal(False)
        self.copy_btn.setEnabled(False)

        # Create a QStackedWidget
        self.stacked_widget = QStackedWidget()

        # Create a loading message
        self.loading_pane = EmptyMessageWidget(
            self,
            "dependencies",
            _("Dependency information will be retrieved shortly. "
              "Please wait..."),
            bottom_stretch=1,
            spinner=True,
        )

        # Add the loading label and tree widget to the stacked widget
        self.stacked_widget.addWidget(self.loading_pane)
        self.stacked_widget.addWidget(self.treewidget)

        # Make sure the loading label is the one shown initially
        self.stacked_widget.setCurrentWidget(self.loading_pane)

        # Layout
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.copy_btn)
        hlayout.addStretch()
        hlayout.addWidget(ok_btn)

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(*((5 * AppStyle.MarginSize,) * 4))
        vlayout.addWidget(self.stacked_widget)
        vlayout.addSpacing(AppStyle.MarginSize)
        vlayout.addWidget(label)
        vlayout.addSpacing((-2 if MAC else 1) * AppStyle.MarginSize)
        vlayout.addLayout(hlayout)

        self.setLayout(vlayout)
        self.setFixedSize(860, 560)

        # Signals
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        ok_btn.accepted.connect(self.accept)

    def set_data(self, dependencies):
        self.treewidget.update_dependencies(dependencies)
        self.treewidget.resize_columns_to_contents()

        # Once data is loaded, switch to the tree widget
        self.stacked_widget.setCurrentWidget(self.treewidget)

        # Enable copy button
        self.copy_btn.setEnabled(True)

    def copy_to_clipboard(self):
        from spyder.dependencies import status

        QApplication.clipboard().setText(status())


def test():
    """Run dependency widget test"""
    from spyder import dependencies

    # Test sample
    dependencies.add("IPython", "IPython", "Enhanced Python interpreter",
                     ">=20.0")
    dependencies.add("matplotlib", "matplotlib", "Interactive data plotting",
                     ">=1.0")
    dependencies.add("sympy", "sympy", "Symbolic Mathematics", ">=10.0",
                     kind=OPTIONAL)
    dependencies.add("foo", "foo", "Non-existent module", ">=1.0")
    dependencies.add("numpy", "numpy",  "Edit arrays in Variable Explorer",
                     ">=0.10", kind=OPTIONAL)

    from spyder.utils.qthelpers import qapplication
    app = qapplication()  # noqa
    dlg = DependenciesDialog(None)
    dlg.set_data(dependencies.DEPENDENCIES)
    dlg.show()
    sys.exit(dlg.exec_())


if __name__ == '__main__':
    test()
