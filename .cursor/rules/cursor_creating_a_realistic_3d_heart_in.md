# Creating a Realistic 3D Heart in Three.js
_Exported on 5/29/2025 at 10:57:31 GMT+5:30 from Cursor (0.50.5)_

---

**User**

I want you to create a human heart using three js. Make it realistic and use reference from the image attached along with this conversation to create the 3D model. Start with a low-poly technique and then iterate over it to enhance.

---

**Cursor**

Here’s how you can get started with a low-poly human heart in Three.js, referencing the anatomical structure and chamber layout from your image. I’ll give you a basic scaffold for a low-poly heart, then explain how to iterate for realism.

**Step 1: Low-Poly Heart Base (Three.js + basic geometry)**

```js
// Assuming you have a Three.js scene, camera, and renderer set up

// Heart body (main mass)
const heartGeometry = new THREE.SphereGeometry(2, 8, 8); // low-poly sphere
const heartMaterial = new THREE.MeshStandardMaterial({ color: 0xb22222, flatShading: true });
const heartMesh = new THREE.Mesh(heartGeometry, heartMaterial);
heartMesh.scale.set(1, 1.2, 0.8); // elongate for heart shape
scene.add(heartMesh);

// Left ventricle bulge
const lvGeometry = new THREE.SphereGeometry(1, 8, 8);
const lvMesh = new THREE.Mesh(lvGeometry, heartMaterial);
lvMesh.position.set(0.7, -0.5, 0);
lvMesh.scale.set(1.1, 1.2, 1);
scene.add(lvMesh);

// Right ventricle bulge
const rvGeometry = new THREE.SphereGeometry(0.8, 8, 8);
const rvMesh = new THREE.Mesh(rvGeometry, heartMaterial);
rvMesh.position.set(-0.7, -0.5, 0);
rvMesh.scale.set(1, 1.1, 1);
scene.add(rvMesh);

// Aorta (top tube)
const aortaGeometry = new THREE.CylinderGeometry(0.3, 0.3, 2, 8);
const aortaMaterial = new THREE.MeshStandardMaterial({ color: 0xff6347, flatShading: true });
const aortaMesh = new THREE.Mesh(aortaGeometry, aortaMaterial);
aortaMesh.position.set(0, 1.5, 0);
aortaMesh.rotation.z = Math.PI / 6;
scene.add(aortaMesh);

// Pulmonary artery (side tube)
const paGeometry = new THREE.CylinderGeometry(0.25, 0.25, 1.5, 8);
const paMaterial = new THREE.MeshStandardMaterial({ color: 0x4682b4, flatShading: true });
const paMesh = new THREE.Mesh(paGeometry, paMaterial);
paMesh.position.set(-1, 1, 0);
paMesh.rotation.z = -Math.PI / 4;
scene.add(paMesh);

// Add lighting
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 10, 7.5);
scene.add(light);
```

**Step 2: Iterate for Realism**
- Use more segments in your geometries (increase the 8s to 16 or 32).
- Sculpt the heart shape using `THREE.BufferGeometry` and morph targets.
- Add more tubes for veins/arteries (superior/inferior vena cava, pulmonary veins).
- Use textures and bump maps for surface detail.
- Animate the heart (scale up/down for a beating effect).

**Step 3: Reference the Image**
- Position the chambers and vessels as in your diagram.
- Color code the arteries/veins as in the image.
- Add labels or tooltips for pressures if needed.

**Next Steps**
Let me know if you want the next iteration (higher poly, more anatomical detail, or animation). I can also help you with loading a more detailed heart model (e.g., from Blender or an OBJ/GLTF file) if you want to skip manual geometry.

**Summary:**  
You get a low-poly heart with basic chambers and vessels, matching the anatomical layout in your image. Iterate by increasing geometry detail, adding vessels, and using textures for realism. Want the next step?

```javascript
// Assuming you have a Three.js scene, camera, and renderer set up

// Heart body (main mass)
const heartGeometry = new THREE.SphereGeometry(2, 8, 8); // low-poly sphere
const heartMaterial = new THREE.MeshStandardMaterial({ color: 0xb22222, flatShading: true });
const heartMesh = new THREE.Mesh(heartGeometry, heartMaterial);
heartMesh.scale.set(1, 1.2, 0.8); // elongate for heart shape
scene.add(heartMesh);

// Left ventricle bulge
const lvGeometry = new THREE.SphereGeometry(1, 8, 8);
const lvMesh = new THREE.Mesh(lvGeometry, heartMaterial);
lvMesh.position.set(0.7, -0.5, 0);
lvMesh.scale.set(1.1, 1.2, 1);
scene.add(lvMesh);

// Right ventricle bulge
const rvGeometry = new THREE.SphereGeometry(0.8, 8, 8);
const rvMesh = new THREE.Mesh(rvGeometry, heartMaterial);
rvMesh.position.set(-0.7, -0.5, 0);
rvMesh.scale.set(1, 1.1, 1);
scene.add(rvMesh);

// Aorta (top tube)
const aortaGeometry = new THREE.CylinderGeometry(0.3, 0.3, 2, 8);
const aortaMaterial = new THREE.MeshStandardMaterial({ color: 0xff6347, flatShading: true });
const aortaMesh = new THREE.Mesh(aortaGeometry, aortaMaterial);
aortaMesh.position.set(0, 1.5, 0);
aortaMesh.rotation.z = Math.PI / 6;
scene.add(aortaMesh);

// Pulmonary artery (side tube)
const paGeometry = new THREE.CylinderGeometry(0.25, 0.25, 1.5, 8);
const paMaterial = new THREE.MeshStandardMaterial({ color: 0x4682b4, flatShading: true });
const paMesh = new THREE.Mesh(paGeometry, paMaterial);
paMesh.position.set(-1, 1, 0);
paMesh.rotation.z = -Math.PI / 4;
scene.add(paMesh);

// Add lighting
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 10, 7.5);
scene.add(light);
```

---

**User**

I would like to run this in a browser as well please add a rendering layer to it as well

