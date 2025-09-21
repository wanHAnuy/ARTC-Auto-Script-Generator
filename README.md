# ARTC Auto Script Generator

![ARTC Logo](logo.png)

A PyQt5-based GUI application for generating customized Abaqus scripts with 3D visualization of crystal lattice structures.

**Advanced Features**: Hierarchical file organization, batch execution, Transform slider control, and automated output management.

## Features

### 🎨 Modern GUI Interface
- Clean, modern interface with gradient backgrounds and custom logo
- Real-time 3D visualization of crystal structures
- Interactive parameter selection with dropdowns and checkboxes
- **Transform slider** for structure deformation control (0-8 values)
- **Batch mode** with checkbox for continuous execution
- Resizable split-panel layout

### 📐 3D Visualization
- Interactive 3D plots showing crystal structure geometry
- Real-time updates when changing cell types
- Connected points visualization with lines showing lattice connections
- Support for multiple crystal structures:
  - Cubic, BCC, FCC, FCCZ
  - Octet-truss, Tetrahedron-base
  - Diamond, Octahedron, Rhombic
  - Auxetic, G7, FBCCZ, FBCCXYZ
  - And more...

### 🔧 Advanced Script Generation & File Management
- **Automated Abaqus Python script generation** with intelligent file organization
- **5-Level Hierarchical Folder Structure**:
  ```
  generate_script/
  ├── {CellType}/                     # Level 1: Structure type
  │   ├── {CellType}_{Mode}/          # Level 2: + Analysis mode
  │   │   ├── {CellType}_{Size}_{Mode}/   # Level 3: + Cell size
  │   │   │   ├── {CellType}_{Size}_{Radius}_{Mode}/  # Level 4: + Radius
  │   │   │   │   └── {CellType}_{Size}_{Radius}_{Slider}_{Mode}/  # Level 5: + Transform
  │   │   │   │       ├── script.py
  │   │   │   │       ├── Job-1.odb    # Output files in same directory
  │   │   │   │       └── Job-1.dat
  ```

- **Multi-template approach**:
  - `strut_FCCZ_static.py` - Default static analysis template
  - `strut_FCCZ_Dynamic.py` - Dynamic analysis template (Speed On)
  - `strut_FCCZ_direction.py` - Directional analysis template (Direction On)

- **Automatic Batch Execution System**:
  - **`run_all_scripts.py`** automatically generated in each folder
  - Recursively finds and executes all .py scripts
  - User confirmation before execution
  - Progress tracking and error handling
  - Execution statistics and timing

- **Transform Slider Control**:
  - **Slider range**: 0-8 for structure deformation
  - **Batch mode**: Check Transform checkbox to run all 9 variations (0-8)
  - **Real-time visualization** updates with slider changes
  - Structure-specific deformation algorithms

- **Smart Output Management**:
  - **Job files save location**: Same directory as script file
  - **Automatic directory creation** for each configuration
  - **No file conflicts** - each run gets its own folder

- **Dynamic parameter substitution**:
  - **Cell Type**: Changes crystal structure geometry
  - **Cell Size**: Scales coordinates proportionally (3, 4, 5, 7, 9, 11, 13)
  - **Cell Strut Radius**: Adjusts cylinder radius (0.3-0.5)
  - **Transform Slider**: Structure deformation control (0-8)
  - **Speed**: Velocity parameters for dynamic analysis (10, 100, 1000)
  - **Directions**: Directional constraints (X, Y, Z)

- **Intelligent file naming**: `{CellType}_{CellSize}_{CellRadius}_{Slider}_{Mode}.py`

## Project Structure

```
Auto_script/
├── main.py                           # Main application entry point
├── qt_interface.py                  # GUI interface and main window
├── visualization_widget.py          # 3D visualization component
├── script_generator.py              # Abaqus script generation engine (Enhanced)
├── structure_set.py                 # Crystal structure definitions
├── macro_integration.py             # Macro functionality integrator
├── strut_FCCZ_static.py            # Static analysis template (default)
├── strut_FCCZ_Dynamic.py           # Dynamic analysis template (Speed On)
├── strut_FCCZ_direction.py         # Directional analysis template (Direction On)
├── logo.ico                         # Application icon
├── logo.png                         # Application logo for README
├── generate_script/                 # Hierarchical output directory
│   ├── run_all_scripts.py          # Auto-generated batch executor
│   └── [Hierarchical folders...]    # 5-level organized structure
└── README.md                        # This file
```

## Installation & Dependencies

### Required Packages
```bash
pip install PyQt5
pip install matplotlib
pip install numpy
```

### Building Executable
```bash
# Complete build command with all dependencies
pyinstaller --onefile --windowed --name "ScriptGenerator" --icon "logo.ico" --add-data "logo.ico;." --add-data "strut_FCCZ_static.py;." --add-data "strut_FCCZ_Dynamic.py;." --add-data "strut_FCCZ_direction.py;." --add-data "structure_set.py;." --add-data "macro_integration.py;." --add-data "qt_interface.py;." --add-data "script_generator.py;." --add-data "visualization_widget.py;." --version-file version_info.txt main.py

# Or use the spec file (recommended)
pyinstaller ScriptGenerator.spec
```

### System Requirements
- Python 3.6+
- Windows/Linux/macOS
- Abaqus (for running generated scripts)

## Usage

### Running the Application
```bash
python main.py
```

### Using the Interface

#### Single Script Generation
1. **Select Parameters**:
   - Choose cell type from dropdown (affects 3D visualization in real-time)
   - Set cell size (3, 4, 5, 7, 9, 11, or 13 units)
   - Set cell strut radius (0.3, 0.4, or 0.5)
   - Adjust **Transform slider** (0-8) for structure deformation
   - Use checkboxes for Speed and Directions options

2. **Generate Script**:
   - Click "Generate Script" button
   - Script saved in hierarchical folder: `generate_script/{CellType}/{CellType}_{Mode}/{CellType}_{Size}_{Mode}/{CellType}_{Size}_{Radius}_{Mode}/{CellType}_{Size}_{Radius}_{Slider}_{Mode}/`
   - **`run_all_scripts.py`** automatically created for batch execution
   - Button shows generation status and filename

#### Batch Mode (Transform Variations)
1. **Enable Batch Mode**:
   - Check the **Transform checkbox** (button turns black with red text)
   - Click "Generate Script" to start batch generation

2. **Batch Process**:
   - Automatically generates 9 scripts (slider values 0-8)
   - Creates hierarchical folder structure for each variation
   - Button shows progress: "running... 1/9", "running... 2/9", etc.
   - Each script gets its own folder with batch executor

#### 3D Visualization
- **Real-time updates** when changing cell type or Transform slider
- Red points represent lattice nodes
- Blue lines show structural connections
- Interactive 3D plot (rotate, zoom, pan)
- **Transform slider** shows structure deformation in real-time

#### Batch Execution
1. **Navigate** to generate_script folder or any subfolder
2. **Run** `python run_all_scripts.py`
3. **Confirm** execution when prompted
4. **Monitor** progress with detailed status updates
5. **Review** execution statistics and results

## Configuration Parameters

### Cell Types Supported
- **Cubic**: Basic cubic lattice
- **BCC**: Body-Centered Cubic with center connections
- **FCC**: Face-Centered Cubic with face center points
- **FCCZ**: FCC with additional Z-direction connections
- **Octet-truss**: Octet truss structure
- **Tetrahedron-base**: Tetrahedral geometry
- **Diamond**: Diamond crystal structure
- **And 10+ more structures...**

### Cell Sizes
- **3**: Compact structure (coordinates scaled by 0.6x)
- **4**: Medium structure (coordinates scaled by 0.8x)
- **5**: Standard structure (coordinates scaled by 1.0x)
- **7, 9, 11, 13**: Extended structures (coordinates scaled proportionally)

### Transform Slider
- **Range**: 0-8 (9 discrete values)
- **Function**: Controls structure deformation parameters
- **Batch Mode**: When Transform checkbox is enabled, generates all 9 variations
- **Real-time**: Updates 3D visualization as slider moves

### Cell Strut Radius
- **0.3**: Thin struts
- **0.4**: Medium struts
- **0.5**: Thick struts

## Generated Script Features

### Core Script Capabilities
The generated Abaqus Python scripts include:
- Complete material definitions
- Geometric modeling with cylinders
- Assembly and part creation
- Automatic structure-specific interaction setup
- Contact surface definitions based on crystal structure
- Integrated macro functionality for each structure type
- Boundary conditions
- Mesh generation
- Analysis setup

### **NEW**: Enhanced Output Management
- **Job directory auto-configuration**: All output files (.odb, .dat, .msg, etc.) save to script directory
- **No file conflicts**: Each configuration gets its own isolated folder
- **Organized results**: Easy to locate and manage output files

### **NEW**: Batch Execution System
- **Automatic executor generation**: `run_all_scripts.py` created with every folder
- **Recursive script discovery**: Finds all .py files in current and subdirectories
- **Safe execution**: User confirmation required before running
- **Progress monitoring**: Real-time status updates and execution statistics
- **Error handling**: Timeout protection (1 hour per script) and error reporting
- **Abaqus integration**: Uses `abaqus cae noGUI=script.py` command

### Macro Integration Details
Each generated script automatically includes:
- Base geometry creation (from template)
- Structure-specific macro functions (from `interection_marco/`)
- Automatic contact surface identification
- Interaction property assignments
- Structure-optimized boundary conditions

### Example Generated File Structure
```
generate_script/
├── run_all_scripts.py                    # Root batch executor
├── BCC/
│   ├── BCC_static/
│   │   ├── BCC_4_static/
│   │   │   ├── BCC_4_0.4_static/
│   │   │   │   ├── BCC_4_0.4_0_static/
│   │   │   │   │   ├── BCC_4_0.4_0_static.py      # Generated script
│   │   │   │   │   ├── run_all_scripts.py         # Batch executor
│   │   │   │   │   ├── Job-1.odb                  # Abaqus output files
│   │   │   │   │   └── Job-1.dat
│   │   │   │   ├── BCC_4_0.4_1_static/
│   │   │   │   │   └── [similar structure...]
│   │   │   │   └── ... (up to BCC_4_0.4_8_static)
└── FCC/
    └── [similar hierarchical structure...]
```

### File Naming Convention
- **Script files**: `{CellType}_{Size}_{Radius}_{Slider}_{Mode}.py`
- **Examples**:
  - `BCC_4_0.4_3_static.py` - BCC, size 4, radius 0.4, transform 3, static mode
  - `FCC_5_0.5_7_Dynamic.py` - FCC, size 5, radius 0.5, transform 7, dynamic mode
  - `Diamond_3_0.3_0_X.py` - Diamond, size 3, radius 0.3, transform 0, X-direction

### Supported Crystal Structure Types (20+)
All structures have corresponding macro files for automatic interaction setup:
- **AFCC, Auxetic, BCC, BCCZ** - Basic lattice structures
- **Cubic, Cuboctahedron, Diamond** - Cubic-based geometries
- **FBCCXYZ, FBCCZ, FCC, FCCZ** - Face-centered structures
- **G7, Iso_truss, Kelvin** - Advanced truss structures
- **Octahedron, Octet_truss** - Octahedral geometries
- **Rhombic, Tetrahedron_base** - Angular structures
- **Truncated_cube, Truncated_Octoctahedron** - Truncated forms

## Technical Architecture

### Core Components

1. **ModernInterface** (`qt_interface.py`)
   - Main window and UI management
   - Parameter collection and validation
   - Script generation triggering

2. **CellVisualizationWidget** (`visualization_widget.py`)
   - 3D matplotlib integration
   - Structure geometry calculation
   - Real-time visualization updates

3. **AbaqusScriptGenerator** (`script_generator.py`)
   - Template-based script generation
   - Coordinate scaling algorithms
   - File I/O operations

4. **Crystal Structure Database** (`structure_set.py`)
   - Predefined lattice geometries
   - Connection definitions
   - Coordinate specifications

5. **MacroIntegrator** (`macro_integration.py`) - NEW
   - Maps crystal structures to macro files
   - Extracts and processes macro functions
   - Integrates structure-specific interactions

### Key Algorithms

- **Coordinate Scaling**: Proportional scaling based on cell size
- **Template Substitution**: Regex-based parameter replacement
- **Structure Parsing**: Automatic extraction of coordinates and connections
- **3D Rendering**: matplotlib 3D scatter plots with line connections
- **Hierarchical Path Generation**: 5-level folder structure creation
- **Transform Control**: Slider-based structure deformation algorithms
- **Batch Management**: Automatic script discovery and execution
- **Output Directory Management**: Same-location file saving
- **Macro Integration**: Automatic function extraction and integration
- **Structure-Specific Setup**: Contact surface identification by structure type

## Future Development

### Potential Enhancements
- [ ] Additional crystal structures
- [ ] Custom structure definition interface
- [ ] Animation of structure deformation
- [ ] Export to other CAD formats
- [ ] ✅ **COMPLETED**: Batch script generation with hierarchical organization
- [ ] ✅ **COMPLETED**: Transform slider control and batch execution
- [ ] ✅ **COMPLETED**: Automatic batch executor generation
- [ ] Advanced material property definitions
- [ ] Parallel script execution for batch mode
- [ ] Progress visualization for long-running batches
- [ ] Integration with cloud computing platforms

### Extension Points
- New structures can be added to `structure_set.py`
- Template modifications in `strut_FCCZ_static.py`
- Additional visualization modes in `visualization_widget.py`
- New parameter types in the GUI interface

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Generation Failures**: Check file permissions in output directory
3. **Visualization Not Loading**: Verify matplotlib backend compatibility
4. **Script Errors in Abaqus**: Check coordinate scaling and structure definitions

### Debug Mode
Enable debug output by running:
```bash
python main.py --debug
```

## Logo & Branding

### Application Logo
The ARTC Auto Script Generator features a custom logo design:
- **Logo Files**:
  - `logo.ico` - Application icon (Windows executable)
  - `logo.png` - High-resolution logo for documentation
- **Usage**: Logo appears in application title bar and README documentation
- **Design**: Professional ARTC branding with modern aesthetic

### Logo Integration
- **Application Window**: Logo displayed in window title bar
- **Executable**: Custom icon when built with PyInstaller
- **Documentation**: Logo featured prominently in README header
- **File Association**: Custom icon for generated scripts (when applicable)

## License & Credits

**Developed for ARTC (Advanced Research Technology Center)**
- **Version**: 2.0 (Enhanced with hierarchical organization and batch execution)
- **Created**: 2024
- **Features**: Advanced file management, Transform control, batch processing
- **Platform**: Cross-platform GUI application (Windows/Linux/macOS)

### Development Team
- **Core Development**: ARTC Engineering Team
- **GUI Framework**: PyQt5 with custom styling
- **3D Visualization**: matplotlib integration
- **Script Generation**: Template-based engine with macro integration

For questions, contributions, or technical support, please contact the ARTC development team.

---

*This README provides comprehensive documentation for future development and maintenance of the ARTC Auto Script Generator.*