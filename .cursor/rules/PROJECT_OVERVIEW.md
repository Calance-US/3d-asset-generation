# Project Overview: Realistic 3D Circuit Simulator

## 1. Goal

The primary goal of this project is to create a visually appealing and interactive 3D simulation of a simple electrical circuit. Key features include:
-   Realistic 3D models of common circuit components (battery, resistor, bulb, switch, wires).
-   Interactive switch to toggle the circuit on and off.
-   Visual feedback for the circuit state (e.g., bulb lighting up).
-   Animated visualization of electron flow through the circuit.
-   A focus on achieving a "hyperrealistic" aesthetic for the components.

## 2. Technologies Used

-   **HTML5:** For the basic webpage structure.
-   **CSS3:** For minimal styling of the HTML page.
-   **JavaScript (ES6 Modules):** For all the core logic, 3D rendering, and interactivity.
-   **Three.js (r160):** A comprehensive 3D graphics library for creating and displaying animated 3D computer graphics in a web browser. Used for:
    -   Scene setup (camera, lights, renderer).
    -   Creating 3D geometries for components (cylinders, boxes, spheres, lathes, tubes).
    -   Defining and applying materials (`MeshStandardMaterial` for PBR looks).
    -   Raycasting for mouse interaction (switch clicking).
-   **Tween.js (@21.0.0):** A JavaScript tweening engine for smooth animations (used for the switch lever movement).

## 3. Core Concepts Implemented

-   **Component-Based Design:** Each circuit element is created by a dedicated function in `componentFactory.js`.
-   **Scene Management:** `sceneConfig.js` handles the setup of the Three.js scene, camera, renderer, and lighting.
-   **State Management:** `circuitManager.js` controls the logical state of the circuit (on/off) and updates visual elements accordingly.
-   **Event-Driven Interaction:** Mouse clicks on the switch handle trigger circuit state changes.
-   **Procedural Generation:** 3D models are generated procedurally using Three.js geometries rather than being loaded from external model files.
-   **Electron Flow Visualization:** A custom `ElectronManager` handles the animation of particles along a defined circuit path.

## 4. Desired Aesthetic

The project aims for a "hyperrealistic" look for the components, drawing inspiration from real-world objects. This involved iterative refinement of:
-   Component geometry (adding details like bevels, specific shapes for terminals, intricate filaments).
-   Material properties (`metalness`, `roughness`, `color`, `emissive` properties) to simulate different physical materials (metal, plastic, glass, ceramic).
-   Lighting setup (ambient, directional, point lights, shadow casting) to enhance realism.
-   Specific visual targets were used for some components (e.g., Duracell-style battery, Edison-style bulb). 