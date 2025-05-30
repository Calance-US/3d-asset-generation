# File Structure and Key Responsibilities

This project is organized into several JavaScript files, each with specific responsibilities, along with an `index.html` file as the entry point.

## 1. `index.html`

-   **Role:** Main HTML page that hosts the 3D simulation.
-   **Key Features:**
    -   Sets up the basic page structure and a container `<div>` for the Three.js renderer.
    -   Includes an `importmap` to manage JavaScript module dependencies (Three.js, Tween.js).
    -   Loads `main.js` as the primary script (`type="module"`).
    -   Contains basic CSS for layout and an informational overlay.

## 2. `main.js`

-   **Role:** Orchestrates the entire 3D scene and application logic.
-   **Key Responsibilities:**
    -   Initializes the Three.js scene, camera, renderer, and lighting using helpers from `sceneConfig.js`.
    -   Creates and positions all 3D circuit components (battery, resistor, bulb, switch, wires) by calling functions from `componentFactory.js`.
    -   Sets up `OrbitControls` for camera manipulation.
    -   Creates a workbench surface.
    -   Defines the 3D path for electron flow, creating `THREE.CatmullRomCurve3` segments.
    -   Instantiates `CircuitManager` and `ElectronManager`.
    -   Handles mouse click events for switch interaction (raycasting).
    -   Contains the main animation loop (`animate`) which updates controls, TWEEN animations, the `ElectronManager`, and renders the scene.
    -   Handles window resize events.

## 3. `componentFactory.js`

-   **Role:** Responsible for creating the 3D models (geometry and materials) of all circuit components.
-   **Key Features:**
    -   Defines various `THREE.MeshStandardMaterial` instances for different physical appearances (metals, plastics, glass, ceramic, specific battery colors, bulb glass, etc.).
    -   Contains dedicated functions for creating each component:
        -   `createBattery()`: Constructs a detailed battery model (e.g., Duracell style with black/copper body, terminals).
        -   `createResistor()`: Constructs a resistor model (e.g., bulbous body using `LatheGeometry`, color bands).
        -   `createBulb()`: Constructs a detailed Edison-style bulb (A-shape `LatheGeometry` for glass, brass base, internal stem, complex filament path using `TubeGeometry`).
        -   `createSwitch()`: Constructs a knife switch model (base, copper contacts including U-shape, lever with handle and ferrule).
        -   `createWire()`: Creates cylindrical wire segments.
    -   All component creation functions return a `THREE.Group` containing the component parts, and often specific sub-meshes or materials for interaction (e.g., switch lever, bulb filament material, bulb point light).
    -   Employs a helper `createShadowCastingMesh()` to ensure meshes cast and receive shadows.

## 4. `sceneConfig.js`

-   **Role:** Provides utility functions for setting up the core Three.js scene elements.
-   **Key Responsibilities:**
    -   `createScene()`: Creates the main `THREE.Scene` and sets its background color.
    -   `createRenderer()`: Creates the `THREE.WebGLRenderer`, enables shadow mapping, and sets tone mapping and output color space for better visual quality.
    -   `createCamera()`: Creates a `THREE.PerspectiveCamera` with initial settings.
    -   `createLights()`: Adds various lights to the scene (HemisphereLight, AmbientLight, DirectionalLights) to illuminate the components and enable shadows.

## 5. `circuitManager.js`

-   **Role:** Manages the logical state of the electrical circuit.
-   **Key Responsibilities:**
    -   Tracks whether the circuit is `isCircuitOn`.
    -   Handles the `toggleSwitch()` action:
        -   Animates the switch lever's rotation using TWEEN.js.
        -   Updates the bulb's appearance (filament emissiveness, point light intensity).
        -   Notifies the `ElectronManager` about the change in circuit state (`updateFlowState`).
    -   `updateBulb()`: Modifies the bulb filament material (emissive color, intensity) and the bulb's point light intensity based on the circuit state.

## 6. `electronManager.js`

-   **Role:** Manages the creation, pathing, and animation of electron particles to visualize current flow.
-   **Key Responsibilities:**
    -   Creates a pool of electron particle meshes (small emissive spheres).
    -   `setPathSegments()`: Accepts an array of `THREE.CatmullRomCurve3` objects defining the complete circuit path.
    -   Calculates total path length and individual segment lengths.
    -   `updateFlowState()`: Toggles the visibility and flow of electrons based on whether the circuit is active (switch closed).
    -   `update()`: Called in the main animation loop to move each active electron along the defined path segments. Electrons wrap around the total path for continuous flow. 