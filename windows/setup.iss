; Inno Setup Script for Preview (Document Viewer)
; Developer: Shivam Prasad
; Powered by: TriviLabs.in

#define MyAppName "Preview"
#define MyAppVersion "1.3.1"
#define MyAppPublisher "TriviLabs"
#define MyAppURL "https://trivilabs.in"
#define MyAppExeName "Preview.exe"

[Setup]
AppId={{9FA24D7A-7D9F-4D29-A7FB-DF48E8D9B05F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=Preview-Setup-v{#MyAppVersion}
SetupIconFile=..\preview\assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Preview\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Associate .pdf files (optional user choice)
Root: HKA; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "Preview.Document"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\Preview.Document"; ValueType: string; ValueName: ""; ValueData: "PDF Document"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Preview.Document\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\Preview.Document\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
