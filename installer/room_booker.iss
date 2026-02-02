#define AppName "Room Booker Pro"
#define AppVersion "4.0"
#define AppPublisher "Noxist"
#define AppExeName "RoomBookerPro.exe"

[Setup]
AppId={{YOUR-GUID-HERE-GENERATE-NEW-ONE}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
; Icon für den Installer selbst
SetupIconFile=..\assets\icons\app.ico
OutputDir=..\dist
OutputBaseFilename=RoomBooker_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Erlaubt dem User den Pfad zu ändern
DisableDirPage=no 

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Kopiere ALLES aus dem dist/RoomBookerPro Ordner
Source: "..\dist\RoomBookerPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#AppExeName}"

[Run]
; Checkbox am Ende "App jetzt starten"
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
