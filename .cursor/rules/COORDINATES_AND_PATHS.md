# Key Coordinates and Electron Path Details (Snapshot)

This document provides a snapshot of the critical coordinates used for component placement and the electron flow path definition in `main.js`. **Note:** These values are specific to the current state of component geometries and layout. Any changes to component dimensions, origins, or scene positions in `componentFactory.js` or `main.js` would require these coordinates to be recalculated and updated.

## 1. Component Positions in `main.js` (Square Layout)

All components are generally placed at `Y = 0.5`.

-   **Battery:**
    -   Position: `(0, 0.5, 3)`
    -   Rotation: `battery.rotation.z = Math.PI / 2;` (lays flat along X-axis)

-   **Resistor:**
    -   Position: `(3, 0.5, 0)`
    -   Rotation: Default (leads align along Z-axis due to factory setup and group rotation `group.rotation.x = Math.PI / 2` in `createResistor`)

-   **Bulb:**
    -   Position: `(0, 0.5, -3)`
    -   Rotation: Default

-   **Switch:**
    -   Position: `(-3, 0.5, 0)`
    -   Rotation: `switchComponent.group.rotation.y = 0;` (aligns switch along Z-axis)

## 2. Wire Connection Points in `main.js`

These are the `startPoint` and `endPoint` arguments for `createWire()` calls in `main.js`.

1.  **Battery (+) to Resistor (top lead):**
    -   Start: `new THREE.Vector3(0.8, 0.5, 3)`
    -   End: `new THREE.Vector3(3, 0.5, 0.7)`

2.  **Resistor (bottom lead) to Bulb (right side of base):**
    -   Start: `new THREE.Vector3(3, 0.5, -0.7)`
    -   End: `new THREE.Vector3(0.2, 0.5, -3)`

3.  **Bulb (left side of base) to Switch (contact 1 - non-pivot/closing contact):**
    -   Start: `new THREE.Vector3(-0.2, 0.5, -3)`
    -   End: `new THREE.Vector3(-3, 0.5, -0.5)`

4.  **Switch (contact 2 - pivot) to Battery (-):**
    -   Start: `new THREE.Vector3(-3, 0.5, 0.5)`
    -   End: `new THREE.Vector3(-0.75, 0.5, 3)`

## 3. Electron Flow Path Segments in `main.js`

Electron flow is from Battery Negative to Battery Positive. Intermediate points use `Y = 0.54` for a slight offset, while connection points are at `Y = 0.5`.

**Segment 1: Battery Negative to Switch Pivot (Contact 2)**
```javascript
points = [
    new THREE.Vector3(-0.75, 0.5, 3.0), // Battery Negative Output
    new THREE.Vector3(-1.5, 0.54, 2.0),  // Intermediate point
    new THREE.Vector3(-2.5, 0.54, 1.0),  // Intermediate point
    new THREE.Vector3(-3.0, 0.5, 0.5)   // Switch Pivot Contact
];
```

**Segment 2: Through Switch Lever (Pivot to Closing Contact)**
```javascript
points = [
    new THREE.Vector3(-3.0, 0.5, 0.5),  // Pivot Point
    new THREE.Vector3(-3.0, 0.54, 0.0),  // Mid-point of lever arm
    new THREE.Vector3(-3.0, 0.5, -0.5)  // Closing Contact Point
];
```

**Segment 3: Switch Closing Contact to Bulb (Left Side)**
```javascript
points = [
    new THREE.Vector3(-3.0, 0.5, -0.5), // Switch Closing Contact
    new THREE.Vector3(-2.0, 0.54, -1.5), // Intermediate
    new THREE.Vector3(-1.0, 0.54, -2.5), // Intermediate
    new THREE.Vector3(-0.2, 0.5, -3.0)  // Bulb Left Side
];
```

**Segment 4: Bulb Filament Path (Placeholder)**
```javascript
const bulbFilamentPoints = [
    new THREE.Vector3(-0.2, 0.5, -3.0), 
    new THREE.Vector3(0.0, 0.54, -3.0),  // Mid-point
    new THREE.Vector3(0.2, 0.5, -3.0)   
];
```

**Segment 5: Bulb (Right Side) to Resistor (Bottom Lead)**
```javascript
points = [
    new THREE.Vector3(0.2, 0.5, -3.0),  // Bulb Right Side
    new THREE.Vector3(1.0, 0.54, -2.0),  // Intermediate
    new THREE.Vector3(2.0, 0.54, -1.0),  // Intermediate
    new THREE.Vector3(3.0, 0.5, -0.7)   // Resistor Bottom Lead
];
```

**Segment 6: Through Resistor Body**
```javascript
points = [
    new THREE.Vector3(3.0, 0.5, -0.7), // Resistor Bottom Lead
    new THREE.Vector3(3.0, 0.54, 0.0),  // Mid-point of resistor
    new THREE.Vector3(3.0, 0.5, 0.7)   // Resistor Top Lead
];
```

**Segment 7: Resistor (Top Lead) to Battery Positive**
```javascript
points = [
    new THREE.Vector3(3.0, 0.5, 0.7),   // Resistor Top Lead
    new THREE.Vector3(2.0, 0.54, 1.5),   // Intermediate
    new THREE.Vector3(1.0, 0.54, 2.5),   // Intermediate
    new THREE.Vector3(0.8, 0.5, 3.0)    // Battery Positive Input
];
``` 