# -*- coding: utf-8 -*-

## \package dbr.dialogs

# MIT licensing
# See: docs/LICENSE.txt


import wx, os
from wx.combo import OwnerDrawnComboBox

from dbr.buttons        import ButtonConfirm
from dbr.custom         import Hyperlink
from dbr.custom         import TextIsEmpty
from dbr.language       import GT
from dbr.log            import Logger
from dbr.moduleaccess   import ModuleAccessCtrl
from dbr.textinput      import MultilineTextCtrlPanel
from dbr.workingdir     import ChangeWorkingDirectory
from globals.bitmaps    import ICON_ERROR
from globals.bitmaps    import ICON_EXCLAMATION
from globals.bitmaps    import ICON_INFORMATION
from globals.project    import project_wildcards
from globals.project    import supported_suffixes


## TODO: Doxygen
class OverwriteDialog(wx.MessageDialog):
    def __init__(self, parent, path):
        wx.MessageDialog.__init__(self, parent, wx.EmptyString,
                style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT)
        
        self.SetYesNoLabels(GT(u'Replace'), GT(u'Cancel'))
        
        filename = os.path.basename(path)
        dirname = os.path.basename(os.path.dirname(path))
        
        self.SetMessage(
            GT(u'A file named "{}" already exists. Do you want to replace it?').format(filename)
        )
        
        self.SetExtendedMessage(
            GT(u'The file already exists in "{}". Replacing it will overwrite its contents.').format(dirname)
        )


## TODO: Doxygen
class StandardDirDialog(wx.DirDialog):
    def __init__(self, parent, title, style=wx.DD_DEFAULT_STYLE):
        
        # Setting os.getcwd() causes dialog to always be opened in working directory
        wx.DirDialog.__init__(self, parent, title, os.getcwd(),
                style=style|wx.DD_DIR_MUST_EXIST|wx.DD_NEW_DIR_BUTTON|wx.DD_CHANGE_DIR)
        
        # FIXME: Find inherited bound event
        self.Bind(wx.EVT_BUTTON, self.OnAccept)
        
        self.CenterOnParent()
    
    
    ## TODO: Doxygen
    def OnAccept(self, event=None):
        path = self.GetPath()
        
        if os.path.isdir(path):
            self.EndModal(wx.ID_OK)
            return
        
        # FIXME: Use Logger
        print(u'DEBUG: [dbr.dialogs] Path is not a directory: {}'.format(path))


## TODO: Doxygen
class StandardFileDialog(wx.FileDialog):
    def __init__(self, parent, title, default_extension=wx.EmptyString,
                wildcard=wx.FileSelectorDefaultWildcardStr, style=wx.FD_DEFAULT_STYLE):
        
        # Setting os.getcwd() causes dialog to always be opened in working directory
        wx.FileDialog.__init__(self, parent, title, os.getcwd(), wildcard=wildcard, style=style)
        
        self.extension = default_extension
        
        # FIXME: Should use ID_SAVE & ID_OPEN
        self.Bind(wx.EVT_BUTTON, self.OnAccept)
        
        self.CenterOnParent()
    
    
    ## TODO: Doxygen
    def GetDirectory(self, directory=None):
        if directory == None:
            directory = self.GetPath()
        
        # Recursively check for first directory in hierarchy
        if not os.path.isdir(directory):
            return self.GetDirectory(os.path.dirname(directory))
        
        return directory
    
    
    ## TODO: Doxygen
    def GetExtension(self):
        return self.extension
    
    
    ## FIXME: Seems to be being called 3 times
    def GetFilename(self, *args, **kwargs):
        filename = wx.FileDialog.GetFilename(self, *args, **kwargs)
        
        # Allow users to manually set filename extension
        if not self.HasExtension(filename):
            if not filename.split(u'.')[-1] == self.extension:
                filename = u'{}.{}'.format(filename, self.extension)
        
        return filename
    
    
    ## Fixme: Seems to be being called twice
    def GetPath(self, *args, **kwargs):
        path = wx.FileDialog.GetPath(self, *args, **kwargs)
        
        if len(path):
            if path[-1] == u'.':
                name_error = wx.MessageDialog(wx.GetApp().GetTopWindow(), GT(u'Error'),
                        style=wx.ICON_ERROR|wx.OK)
                
                name_error.SetExtendedMessage(GT(u'Name cannot end with "{}"').format(path[-1]))
                name_error.ShowModal()
                
                return None
        
        out_dir = os.path.dirname(path)
        return u'{}/{}'.format(out_dir, self.GetFilename())
    
    
    ## TODO: Doxygen
    def HasExtension(self, path):
        if u'.' in path:
            if path.split(u'.')[-1] != u'':
                return True
        
        return False
    
    
    ## TODO: Doxygen
    def OnAccept(self, event=None):
        path = self.GetPath()
        
        if path:
            if os.path.isfile(path):
                overwrite = OverwriteDialog(wx.GetApp().GetTopWindow(), path).ShowModal()
                
                if overwrite != wx.ID_YES:
                    return
                
                os.remove(path)
            
            # File & directory dialogs should call this function
            ChangeWorkingDirectory(self.GetDirectory())
            
            self.EndModal(wx.ID_OK)


# FIXME: Unneeded?
class StandardFileSaveDialog(StandardFileDialog):
    def __init__(self, parent, title, default_extension=wx.EmptyString,
            wildcard=wx.FileSelectorDefaultWildcardStr):
        
        # Initialize parent class
        StandardFileDialog.__init__(self, parent, title, default_extension=default_extension,
                wildcard=wildcard, style=wx.FD_SAVE)


# FIXME: Unneded?
class StandardFileOpenDialog(StandardFileDialog):
    def __init__(self, parent, title, default_extension=wx.EmptyString,
            wildcard=wx.FileSelectorDefaultWildcardStr):
        
        # Initialize parent class
        StandardFileDialog.__init__(self, parent, title, default_extension=default_extension,
                wildcard=wildcard, style=wx.FD_OPEN)
    
    
    ## TODO: Doxygen
    def OnAccept(self, event=None):
        # File & directory dialogs should call this function
        ChangeWorkingDirectory(self.GetDirectory())
        
        self.EndModal(wx.ID_OK)


# *** MESSAGE & ERROR *** #

## Displays a dialog with message & details
#  
#  FIXME: Crashes if icon is wx.NullBitmap
#  \param parent
#        \b \e wx.Window : The parent window
#  \param title
#        \b \e unicode|str : Text to display in title bar
#  \param icon
#        \b \e wx.Bitmap|unicode|str : Image to display
class DetailedMessageDialog(wx.Dialog):
    def __init__(self, parent, title=GT(u'Message'), icon=wx.NullBitmap, text=wx.EmptyString,
            details=wx.EmptyString, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title, style=style)
        
        # Allow using strings for 'icon' argument
        if isinstance(icon, (unicode, str)):
            icon = wx.Bitmap(icon)
        
        icon = wx.StaticBitmap(self, wx.ID_ANY, icon)
        
        txt_message = wx.StaticText(self, label=text)
        
        btn_confirm = ButtonConfirm(self)
        
        # self.details needs to be empty for constructor
        self.details = wx.EmptyString
        details = details
        
        # *** Layout *** #
        
        self.lyt_urls = wx.BoxSizer(wx.VERTICAL)
        
        lyt_main = wx.GridBagSizer(5, 5)
        lyt_main.SetCols(3)
        lyt_main.AddGrowableRow(3)
        lyt_main.AddGrowableCol(2)
        lyt_main.Add(icon, (0, 0), (5, 1), wx.ALIGN_TOP|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)
        lyt_main.Add(txt_message, (0, 1), (1, 2), wx.RIGHT|wx.TOP, 20)
        lyt_main.Add(self.lyt_urls, (1, 1), (1, 2), wx.RIGHT, 5)
        lyt_main.Add(btn_confirm, (4, 2),
                flag=wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM|wx.RIGHT|wx.TOP|wx.BOTTOM, border=5)
        
        self.SetAutoLayout(True)
        self.SetSizer(lyt_main)
        
        if not TextIsEmpty(details):
            # self.details will be set here
            self.CreateDetailedView(details)
        
        else:
            self.Layout()
            
            self.Fit()
            self.SetMinSize(self.GetSize())
        
        self.CenterOnParent()
    
    
    ## Adds a clickable link to the dialog
    def AddURL(self, url):
        if not isinstance(url, Hyperlink):
            url = Hyperlink(self, wx.ID_ANY, label=url, url=url)
        
        self.lyt_urls.Add(url, 0, wx.ALIGN_CENTER_VERTICAL)
        
        self.Layout()
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.CenterOnParent()
    
    
    ## Adds buttons & details text to dialog
    #  
    #  \param details
    #        \b \e unicode|str : Detailed text to show in dialog
    def CreateDetailedView(self, details):
        # Controls have not been constructed yet
        if TextIsEmpty(self.details):
            self.btn_details = wx.ToggleButton(self, label=GT(u'Details'))
            #btn_copy = wx.Button(self, label=GT(u'Copy details'))
            
            self.dsp_details = MultilineTextCtrlPanel(self, value=details,
                    style=wx.TE_READONLY)
            
            # *** Event handlers *** #
            
            self.btn_details.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleDetails)
            #btn_copy.Bind(wx.EVT_BUTTON, self.OnCopyDetails)
            
            layout = self.GetSizer()
            layout.Add(self.btn_details, (2, 1))
            #layout.Add(btn_copy, (2, 2), flag=wx.ALIGN_LEFT|wx.RIGHT, border=5)
            layout.Add(self.dsp_details, (3, 1), (1, 2), wx.EXPAND|wx.RIGHT, 5)
            
            self.ToggleDetails()
        
        if not TextIsEmpty(details):
            for C in self.GetChildren():
                if isinstance(C, MultilineTextCtrlPanel):
                    self.details = details
                    C.SetValue(self.details)
                    
                    return True
        
        return False
    
    
    ## TODO: Doxygen
    #  
    #  FIXME: Layout initially wrong
    #  TODO: Allow copying details to clipboard
    def OnCopyDetails(self, event=None):
        print(u'DEBUG: Copying details to clipboard ...')
        
        DetailedMessageDialog(self, u'FIXME', ICON_EXCLAMATION,
                u'Copying details to clipboard not functional').ShowModal()
        return
        
        cb_set = False
        
        clipboard = wx.Clipboard()
        if clipboard.Open():
            print(u'DEBUG: Clipboard opened')
            
            details = wx.TextDataObject(self.dsp_details.GetValue())
            print(u'DEBUG: Details set to:\n{}'.format(details.GetText()))
            
            clipboard.Clear()
            print(u'DEBUG: Clipboard cleared')
            
            cb_set = clipboard.SetData(details)
            print(u'DEBUG: Clipboard data set')
            
            clipboard.Flush()
            print(u'DEBUG: Clipboard flushed')
            
            clipboard.Close()
            print(u'DEBUG: Clipboard cloased')
        
        del clipboard
        print(u'DEBUG: Clipboard object deleted')
        
        wx.MessageBox(GT(u'FIXME: Details not copied to clipboard'), GT(u'Debug'))
    
    
    ## TODO: Doxygen
    def SetDetails(self, details):
        return self.CreateDetailedView(details)
    
    
    ## TODO: Doxygen
    def ToggleDetails(self, event=None):
        try:
            if self.btn_details.GetValue():
                self.dsp_details.Show()
            
            else:
                self.dsp_details.Hide()
            
            self.Layout()
            self.Fit()
            self.SetMinSize(self.GetSize())
            
            return True
        
        except AttributeError:
            # Disable toggling details
            self.btn_details.Hide()
            
            self.Layout()
            self.Fit()
            self.SetMinSize(self.GetSize())
            
            return False


## Message dialog that shows an error & details
class ErrorDialog(DetailedMessageDialog):
    def __init__(self, parent, text, details=wx.EmptyString):
        DetailedMessageDialog.__init__(self, parent, GT(u'Error'), ICON_ERROR, text, details)


## TODO: Doxygen
class SuperUserDialog(wx.Dialog):
    def __init__(self, ID=wx.ID_ANY):
        wx.Dialog.__init__(self, wx.GetApp().GetTopWindow(), ID)
        
        # User selector
        self.users = OwnerDrawnComboBox(self)


## TODO: Doxygen
def GetDialogWildcards(ID):
    proj_def = project_wildcards[ID][0]
    wildcards = list(project_wildcards[ID][1])
    
    for X in range(len(wildcards)):
        wildcards[X] = u'.{}'.format(wildcards[X])
    
    # Don't show list of suffixes in dialog's description
    if project_wildcards[ID][1] != supported_suffixes:
        proj_def = u'{} ({})'.format(proj_def, u', '.join(wildcards))
    
    for X in range(len(wildcards)):
        wildcards[X] = u'*{}'.format(wildcards[X])
    
    return (proj_def, u';'.join(wildcards))


## TODO: Doxygen
def GetDirDialog(main_window, title):
    dir_open = StandardDirDialog(main_window, title)
    
    return dir_open


## TODO: Doxygen
def GetFileOpenDialog(main_window, title, ext_filters, default_extension=None):
    if isinstance(ext_filters, (list, tuple)):
        ext_filters = u'|'.join(ext_filters)
    
    file_open = StandardFileOpenDialog(main_window, title, wildcard=ext_filters)
    
    return file_open


## Retrieves a dialog for display
#  
#  If 'Use custom dialogs' is selected from
#    the main window, the a custom defined
#    dialog is returned. Otherwise the systems
#    default dialog is used.
#    FIXME: Perhaps should be moved to dbr.custom
#  \param main_window
#        Debreate's main window class
#  \param title
#        Text to be shown in the dialogs's title bar
#  \param ext_filter
#        Wildcard to be used to filter filenames
#  \param default_extension
#        The default filename extension to use when opening or closing a file
#          Only applies to custom dialogs
#  \return
#        The dialog window to be shown
def GetFileSaveDialog(main_window, title, ext_filters, extension=None):
    if isinstance(ext_filters, (list, tuple)):
        ext_filters = u'|'.join(ext_filters)
    
    file_save = StandardFileSaveDialog(main_window, title, default_extension=extension,
            wildcard=ext_filters)
    
    return file_save


## Used to display a dialog window
#  
#  For custom dialogs, the method 'DisplayModal()' is used
#    to display the dialog. For stock dialogs, 'ShowModal()'
#    is used. The dialog that will be shown is determined
#    from 'GetFileSaveDialog'.
#    FIXME: Perhaps should be moved to dbr.custom
#  \param main_window
#    Debreate's main window class
#  \param dialog
#    The dialog window to be shown
#  \return
#    'True' if the dialog's return value is 'wx..ID_OK', 'False'
#      otherwise
#  
#  \b Alias: \e dbr.ShowDialog
def ShowDialog(dialog):
    # Dialog's parent should be set to main window
    #debreate = dialog.GetParent()
    
    if False: #debreate.cust_dias.IsChecked():
        return dialog.DisplayModal()
    
    else:
        return dialog.ShowModal() == wx.ID_OK


## Displays an instance of ErrorDialog class
#  
#  \param text
#        \b \e str|unicode: Explanation of error
#  \param details
#        \b \e str|unicode: Extended details of error
#  \param module
#        \b \e str|unicode: Module where error was caught (used for Logger output)
#  \param warn
#        \b \e bool: Show log message as warning instead of error
def ShowErrorDialog(text, details=None, parent=False, warn=False):
    # Instantiate Logger message type so it can be optionally changed
    PrintLogMessage = Logger.Error
    if warn:
        PrintLogMessage = Logger.Warning
    
    logger_text = text
    
    if isinstance(text, (tuple, list)):
        logger_text = u'; '.join(text)
        text = u'\n'.join(text)
    
    if details:
        logger_text = u'{}:\n{}'.format(logger_text, details)
    
    if not parent:
        parent = wx.GetApp().GetTopWindow()
    
    if isinstance(parent, ModuleAccessCtrl):
        module_name = parent.GetModuleName()
    
    else:
        module_name = parent.GetName()
    
    PrintLogMessage(module_name, logger_text)
    
    error_dialog = ErrorDialog(parent, text)
    if details:
        error_dialog.SetDetails(details)
    
    error_dialog.ShowModal()


## A function that displays a modal message dialog on the main window
def ShowMessageDialog(text, title=GT(u'Message'), details=None, module=None):
    main_window = wx.GetApp().GetTopWindow()
    if not module:
        module = main_window.__name__
    
    logger_text = text
    if isinstance(text, (tuple, list)):
        logger_text = u'; '.join(text)
        text = u'\n'.join(text)
    
    if details:
        logger_text = u'{}:\n{}'.format(logger_text, details)
    
    message_dialog = DetailedMessageDialog(main_window, title, ICON_INFORMATION, text)
    if details:
        message_dialog.SetDetails(details)
    
    Logger.Debug(module, logger_text)
    
    message_dialog.ShowModal()
