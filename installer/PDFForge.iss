; PDFForge 1.0.0 per-user setup installer.
; Set PDFFORGE_DIST_DIR to the PyInstaller one-folder output before compiling.

#define AppName "PDFForge"
#define AppVersion "1.0.0"
#define AppPublisher "PDFForge"
#define SourceDir GetEnv("PDFFORGE_DIST_DIR")

#if SourceDir == ""
  #error "Set PDFFORGE_DIST_DIR to the folder containing PDFForge.exe and _internal."
#endif

[Setup]
AppId={{C9D5030C-09D7-4D81-99E6-A1E8674EF6DC}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\PDFForge
DefaultGroupName=PDFForge
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
SetupArchitecture=x64
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\PDFForge.exe
OutputDir={#SourceDir}\..
OutputBaseFilename=PDFForge-Setup-v1.0.0
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\PDFForge.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PDFForge"; Filename: "{app}\PDFForge.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\PDFForge"; Filename: "{app}\PDFForge.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\PDFForge.exe"; Description: "Launch PDFForge"; Flags: nowait postinstall skipifsilent
