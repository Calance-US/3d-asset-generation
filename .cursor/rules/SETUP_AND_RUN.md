# Setup and Running Instructions

## 1. Prerequisites

-   A modern web browser that supports WebGL and ES6 Modules (e.g., Chrome, Firefox, Edge, Safari).
-   Python 3 (for the simple HTTP server to serve files locally).
-   Git (for version control and deployment via GitHub).
-   (Optional) Vercel CLI, if deploying from the command line: `npm install -g vercel`

## 2. Local Development Setup

1.  **Clone the Repository (if applicable):**
    ```bash
    git clone https://github.com/Bhavya2396/circuit-realistic.git
    cd circuit-realistic
    ```
    (If starting from scratch, ensure all project files are in a single directory.)

2.  **Serve the Files:**
    Navigate to the root directory of the project in your terminal and run a simple HTTP server. Using Python 3:
    ```bash
    python3 -m http.server
    ```
    If you have Python 2, the command is `python -m SimpleHTTPServer`.

3.  **View in Browser:**
    Open your web browser and navigate to `http://localhost:8000` (or the port specified by the server, usually 8000).
    You should see the 3D circuit simulation.

## 3. Key Iterative Development Steps (Agent Reference)

If an agent were to replicate this project, the development followed an iterative process, roughly:

1.  **Basic Scene Setup:** (`index.html`, `main.js`, `sceneConfig.js`)
    -   HTML structure, importmap.
    -   Initial Three.js scene, camera, renderer, basic lighting.
    -   OrbitControls.

2.  **Initial Component Creation:** (`componentFactory.js`)
    -   Define basic materials.
    -   Create simple versions of each component (battery, bulb, switch, resistor, wires) using primitive geometries.
    -   Place components in `main.js`.

3.  **Circuit Logic:** (`circuitManager.js`)
    -   Implement switch toggling logic.
    -   Basic bulb on/off visual change (emissive color).
    -   Tween.js animation for the switch lever.

4.  **Layout Refinement:** (Modifications in `main.js`)
    -   Arrange components into the desired square layout.
    -   Update wire connections accordingly.

5.  **Hyperrealistic Detailing - Iteration 1 (Materials & Lighting):**
    -   Refine `MeshStandardMaterial` properties (`metalness`, `roughness`) in `componentFactory.js` for all components.
    -   Enhance lighting in `sceneConfig.js` (ACESFilmicToneMapping, SRGBColorSpace, HemisphereLight).

6.  **Hyperrealistic Detailing - Iteration 2 (Component Geometry & Specific Styles):** (Extensive changes in `componentFactory.js`)
    -   **Battery:** Modeled after Duracell (black/copper body, specific terminal shapes).
    -   **Resistor:** Bulbous body via `LatheGeometry`, updated color bands, end caps removed, leads refined.
    -   **Bulb:** Modeled after Edison bulb (A-shape `LatheGeometry` glass, brass base, internal stem, complex filament via `TubeGeometry`). Added a `PointLight` to the bulb.
    -   **Switch:** Detailed contacts (U-shape, pivot block), added ferrule to handle, refined base material.
    Each component often required defining new, more specific materials.

7.  **Electron Flow Visualization:**
    -   Created `electronManager.js` to handle particle animation along a path.
    -   Defined a multi-segment `CatmullRomCurve3` path in `main.js`, tracing the circuit (negative to positive).
    -   Integrated `ElectronManager` with `CircuitManager` (to start/stop flow) and `main.js` (to update animation).
    -   Iteratively refined path points for better visual alignment (e.g., making flow appear *near* wires).

## 4. Deployment

### Using GitHub Pages (Simple)

1.  Ensure all code is committed and pushed to a GitHub repository.
2.  In the repository settings on GitHub, go to the "Pages" section.
3.  Choose the branch to deploy from (e.g., `main`) and the `/ (root)` folder.
4.  Save. GitHub will provide a URL.

### Using Vercel (Recommended for CI/CD)

1.  **Push to GitHub:** Ensure your project is on GitHub.
    ```bash
    git init # if not already a repo
    git remote add origin <your-repo-url> # if not already set
    git add .
    git commit -m "Ready for Vercel deployment"
    git push origin main
    ```

2.  **Deploy via Vercel Dashboard:**
    -   Sign up/Log in to [vercel.com](https://vercel.com) (can use GitHub account).
    -   Click "Import Project" or "New Project".
    -   Import from the Git repository (`circuit-realistic`).
    -   Vercel usually auto-detects settings for static sites. No special build command or output directory changes are typically needed.
    -   Click "Deploy".

3.  **Deploy via Vercel CLI (as done in the session):**
    -   Install Vercel CLI: `npm install -g vercel`
    -   Log in: `vercel login`
    -   In the project root directory, run: `vercel --prod`
    -   Follow the prompts to link to a new or existing Vercel project.

    Vercel will provide a production URL and set up CI/CD for future pushes to the connected GitHub branch.

## 5. Future Enhancements (Considerations during development)

-   **Dynamic Switch Path for Electrons:** The electron path segment through the switch lever should dynamically update based on the lever's rotation, truly breaking the path when open.
-   **Accurate Bulb Filament Electron Path:** The electron path through the bulb should precisely trace the complex filament geometry.
-   **Texture Mapping:** For ultimate realism, image textures (e.g., wood grain, brushed metal, plastic imperfections) could be applied to components using `TextureLoader` and material maps (`.map`, `.normalMap`, `.roughnessMap`).
-   **User Interface Controls:** Add UI elements to control aspects like electron speed, camera views, etc. 