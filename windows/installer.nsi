; NSIS Modern User Interface Installer Script for Preview (Document Viewer)
; Developer: Shivam Prasad
; Powered by: TriviLabs.in

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "Preview"
OutFile "..\dist\Preview-Setup.exe"
InstallDir "$PROGRAMFILES64\Preview"
InstallDirRegKey HKLM "Software\Preview" "Install_Dir"
RequestExecutionLevel admin

; Interface Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "..\preview\assets\icon.ico"
!define MUI_UNICON "..\preview\assets\icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Preview (required)" SecCore
    SectionIn RO
    SetOutPath "$INSTDIR"
    File /r "..\dist\Preview\*.*"

    ; Write registry keys for uninstaller
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Preview" "DisplayName" "Preview (macOS Document Viewer)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Preview" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Preview" "DisplayIcon" '"$INSTDIR\Preview.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Preview" "Publisher" "TriviLabs"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Preview" "DisplayVersion" "1.7.0"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Preview" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Preview" "NoRepair" 1

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\Preview"
    CreateShortcut "$SMPROGRAMS\Preview\Preview.lnk" "$INSTDIR\Preview.exe" "" "$INSTDIR\Preview.exe" 0
    CreateShortcut "$SMPROGRAMS\Preview\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
    CreateShortcut "$DESKTOP\Preview.lnk" "$INSTDIR\Preview.exe" "" "$INSTDIR\Preview.exe" 0
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\Preview\Preview.lnk"
    Delete "$SMPROGRAMS\Preview\Uninstall.lnk"
    RMDir "$SMPROGRAMS\Preview"
    Delete "$DESKTOP\Preview.lnk"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Preview"
    DeleteRegKey HKLM "Software\Preview"
SectionEnd
