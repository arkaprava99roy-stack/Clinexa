import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export const HeroHelixCanvas: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.z = 7;

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
    scene.add(ambientLight);

    const cyanLight = new THREE.PointLight(0x00f2fe, 4, 50);
    cyanLight.position.set(10, 10, 10);
    scene.add(cyanLight);

    const roseLight = new THREE.PointLight(0xf43f5e, 3, 50);
    roseLight.position.set(-10, -10, -10);
    scene.add(roseLight);

    // 4. Helix Container Group
    const helixGroup = new THREE.Group();
    scene.add(helixGroup);

    // 4a. Translucent Core Cylinder
    const coreGeo = new THREE.CylinderGeometry(0.15, 0.15, 5.5, 32);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.15,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    helixGroup.add(coreMesh);

    // 4b. Double Helix Strands
    const strandGeo = new THREE.SphereGeometry(0.09, 16, 16);
    const cyanMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      emissive: 0x00f2fe,
      emissiveIntensity: 2,
      roughness: 0.2,
      metalness: 0.8,
    });
    const roseMat = new THREE.MeshStandardMaterial({
      color: 0xf43f5e,
      emissive: 0xf43f5e,
      emissiveIntensity: 2,
      roughness: 0.2,
      metalness: 0.8,
    });

    const rungMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.5,
    });

    const pairsCount = 45;
    const heightSpan = 5.0;
    const radius = 1.6;

    for (let i = 0; i < pairsCount; i++) {
      const progress = i / pairsCount;
      const t = progress * Math.PI * 6; // 3 full turns
      const y = progress * heightSpan - heightSpan / 2;

      // Strand A (Cyan)
      const x1 = Math.cos(t) * radius;
      const z1 = Math.sin(t) * radius;
      const sphereA = new THREE.Mesh(strandGeo, cyanMat);
      sphereA.position.set(x1, y, z1);
      helixGroup.add(sphereA);

      // Strand B (Rose/Magenta)
      const x2 = Math.cos(t + Math.PI) * radius;
      const z2 = Math.sin(t + Math.PI) * radius;
      const sphereB = new THREE.Mesh(strandGeo, roseMat);
      sphereB.position.set(x2, y, z2);
      helixGroup.add(sphereB);

      // Rungs connecting strands (every 2nd pair)
      if (i % 2 === 0) {
        const rungLength = radius * 2;
        const rungGeo = new THREE.CylinderGeometry(0.02, 0.02, rungLength, 8);
        const rungMesh = new THREE.Mesh(rungGeo, rungMat);

        rungMesh.position.set(0, y, 0);
        rungMesh.rotation.z = Math.PI / 2;
        rungMesh.rotation.y = -t;
        helixGroup.add(rungMesh);
      }
    }

    // 5. Animation Loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Rotation & gentle float wobble
      helixGroup.rotation.y = elapsedTime * 0.2;
      helixGroup.rotation.x = Math.sin(elapsedTime * 0.15) * 0.15;

      renderer.render(scene, camera);
    };

    animate();

    // 6. Resize Handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 pointer-events-none z-0 overflow-hidden"
    />
  );
};
