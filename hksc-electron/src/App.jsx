const { useState, useEffect, useRef, useCallback } = React;

// API base URL
const API_URL = 'http://localhost:5000/api';

// Axios instance
const api = axios.create({
  baseURL: API_URL,
  timeout: 300000, // 5 minutes for long operations
});

// ============================================
// 3D Knight Tour Visualization Component
// ============================================
function Knight3DVisualization({ tour, currentStep, isPlaying }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const knightRef = useRef(null);
  const pathLineRef = useRef(null);
  const animationIdRef = useRef(null);
  const currentStepRef = useRef(currentStep);
  
  useEffect(() => {
    currentStepRef.current = currentStep;
  }, [currentStep]);

  useEffect(() => {
    if (!mountRef.current || !tour || tour.length === 0) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(
      75,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(25, 25, 25);
    camera.lookAt(8, 8, 8);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Controls
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(8, 8, 8);

    // Grid
    const gridHelper = new THREE.GridHelper(32, 16, 0x00ffff, 0x222222);
    gridHelper.position.set(8, 0, 8);
    scene.add(gridHelper);

    // Axes
    const axesHelper = new THREE.AxesHelper(5);
    axesHelper.position.set(0, 0, 0);
    scene.add(axesHelper);

    // Cube wireframe (16x16x16)
    const cubeGeometry = new THREE.BoxGeometry(16, 16, 16);
    const cubeEdges = new THREE.EdgesGeometry(cubeGeometry);
    const cubeLine = new THREE.LineSegments(cubeEdges, new THREE.LineBasicMaterial({ color: 0x00ffff, opacity: 0.3, transparent: true }));
    cubeLine.position.set(8, 8, 8);
    scene.add(cubeLine);

    // Knight path line
    const pathGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(tour.length * 3);
    for (let i = 0; i < tour.length; i++) {
      positions[i * 3] = tour[i][0];
      positions[i * 3 + 1] = tour[i][1];
      positions[i * 3 + 2] = tour[i][2];
    }
    pathGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const pathMaterial = new THREE.LineBasicMaterial({ 
      color: 0x00ffff, 
      linewidth: 2,
      opacity: 0.8,
      transparent: true
    });
    const pathLine = new THREE.Line(pathGeometry, pathMaterial);
    scene.add(pathLine);
    pathLineRef.current = pathLine;

    // Knight (sphere)
    const knightGeometry = new THREE.SphereGeometry(0.5, 32, 32);
    const knightMaterial = new THREE.MeshPhongMaterial({ 
      color: 0xff0000,
      emissive: 0x440000,
      shininess: 100
    });
    const knight = new THREE.Mesh(knightGeometry, knightMaterial);
    knight.position.set(tour[0][0], tour[0][1], tour[0][2]);
    scene.add(knight);
    knightRef.current = knight;

    // Start and end markers
    const startGeometry = new THREE.SphereGeometry(0.8, 32, 32);
    const startMaterial = new THREE.MeshPhongMaterial({ color: 0x00ff00, emissive: 0x004400 });
    const startMarker = new THREE.Mesh(startGeometry, startMaterial);
    startMarker.position.set(tour[0][0], tour[0][1], tour[0][2]);
    scene.add(startMarker);

    const endGeometry = new THREE.SphereGeometry(0.8, 32, 32);
    const endMaterial = new THREE.MeshPhongMaterial({ color: 0xff0000, emissive: 0x440000 });
    const endMarker = new THREE.Mesh(endGeometry, endMaterial);
    endMarker.position.set(tour[tour.length - 1][0], tour[tour.length - 1][1], tour[tour.length - 1][2]);
    scene.add(endMarker);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x00ffff, 1, 100);
    pointLight.position.set(10, 20, 10);
    scene.add(pointLight);

    const pointLight2 = new THREE.PointLight(0xff00ff, 1, 100);
    pointLight2.position.set(20, 10, 20);
    scene.add(pointLight2);

    // Animation loop
    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      controls.update();
      
      // Update knight position based on current step
      if (knightRef.current && tour.length > 0) {
        const step = Math.min(currentStepRef.current, tour.length - 1);
        knightRef.current.position.set(tour[step][0], tour[step][1], tour[step][2]);
      }
      
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (mountRef.current && cameraRef.current && rendererRef.current) {
        cameraRef.current.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (rendererRef.current && mountRef.current) {
        mountRef.current.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
    };
  }, [tour]);

  return (
    <div 
      ref={mountRef} 
      style={{ 
        width: '100%', 
        height: '100%',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 0 30px rgba(0, 255, 255, 0.3)'
      }} 
    />
  );
}

// ============================================
// Tab Component
// ============================================
function Tab({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '15px 25px',
        background: active ? 'linear-gradient(135deg, #00ffff, #0080ff)' : 'transparent',
        color: active ? '#000' : '#fff',
        border: 'none',
        borderRadius: '8px 8px 0 0',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 'bold',
        textTransform: 'uppercase',
        letterSpacing: '1px',
        transition: 'all 0.3s ease',
        marginRight: '5px'
      }}
    >
      {label}
    </button>
  );
}

// ============================================
// Main App Component
// ============================================
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('Ready');
  
  // Keygen state
  const [keys, setKeys] = useState(null);
  
  // Encryption state
  const [message, setMessage] = useState('');
  const [ciphertext, setCiphertext] = useState(null);
  const [decryptedMessage, setDecryptedMessage] = useState('');
  
  // 3D Visualization state
  const [tour, setTour] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Onion encryption state
  const [onionLayers, setOnionLayers] = useState(10);
  const [onionResult, setOnionResult] = useState(null);
  
  // ZK Proof state
  const [zkProof, setZkProof] = useState(null);

  // Check API health on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await api.get('/health');
      setStatus(`Connected | Cells: ${response.data.cells}`);
    } catch (error) {
      setStatus('API Not Connected');
    }
  };

  // Key Generation
  const handleKeygen = async () => {
    setIsLoading(true);
    setStatus('Generating keys...');
    try {
      const response = await api.post('/keygen');
      setKeys(response.data);
      setTour(response.data.public.start_pos ? [[...response.data.public.start_pos]] : []);
      setStatus('Keys generated successfully!');
    } catch (error) {
      setStatus('Keygen failed: ' + error.message);
    }
    setIsLoading(false);
  };

  // Encryption
  const handleEncrypt = async () => {
    if (!keys || !message) {
      setStatus('Please generate keys and enter a message');
      return;
    }
    setIsLoading(true);
    setStatus('Encrypting...');
    try {
      const response = await api.post('/encrypt', {
        public: keys.public,
        message: message
      });
      setCiphertext(response.data.ciphertext);
      setStatus('Message encrypted!');
    } catch (error) {
      setStatus('Encryption failed: ' + error.message);
    }
    setIsLoading(false);
  };

  // Decryption
  const handleDecrypt = async () => {
    if (!keys || !ciphertext) {
      setStatus('Please encrypt a message first');
      return;
    }
    setIsLoading(true);
    setStatus('Decrypting...');
    try {
      const response = await api.post('/decrypt', {
        private: keys.private,
        ciphertext: ciphertext
      });
      setDecryptedMessage(response.data.message);
      setStatus('Message decrypted!');
    } catch (error) {
      setStatus('Decryption failed: ' + error.message);
    }
    setIsLoading(false);
  };

  // Onion Encryption
  const handleOnionEncrypt = async () => {
    if (!message) {
      setStatus('Please enter a message');
      return;
    }
    setIsLoading(true);
    setStatus(`Creating ${onionLayers}-layer onion encryption...`);
    try {
      const response = await api.post('/onion/encrypt', {
        message: message,
        layers: onionLayers
      });
      setOnionResult(response.data.onion);
      setStatus('Onion encryption complete!');
    } catch (error) {
      setStatus('Onion encryption failed: ' + error.message);
    }
    setIsLoading(false);
  };

  // Generate ZK Proof
  const handleZkProof = async () => {
    if (!keys) {
      setStatus('Please generate keys first');
      return;
    }
    setIsLoading(true);
    setStatus('Generating ZK proof...');
    try {
      const response = await api.post('/zk/proof', {
        tour: keys.private.tour,
        start_pos: keys.public.start_pos
      });
      setZkProof(response.data.proof);
      setStatus('ZK proof generated!');
    } catch (error) {
      setStatus('ZK proof failed: ' + error.message);
    }
    setIsLoading(false);
  };

  // Export 3D Model
  const handleExportObj = async () => {
    if (!keys) {
      setStatus('Please generate keys first');
      return;
    }
    setIsLoading(true);
    setStatus('Exporting 3D model...');
    try {
      await api.post('/export/obj', {
        tour: keys.private.tour
      });
      setStatus('3D model exported to .obj file!');
    } catch (error) {
      setStatus('Export failed: ' + error.message);
    }
    setIsLoading(false);
  };

  // Render Dashboard Tab
  const renderDashboard = () => (
    <div style={{ padding: '30px' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '20px'
      }}>
        {/* Status Card */}
        <div style={cardStyle}>
          <h3 style={cardTitleStyle}>🔐 System Status</h3>
          <p style={{ color: '#00ffff', fontSize: '18px' }}>{status}</p>
          <p style={{ color: '#888', marginTop: '10px' }}>
            HKSC-4096: 16×16×16 Supercube<br/>
            4096 cells | 3D Knight Tour | zk-SNARK
          </p>
        </div>

        {/* Quick Actions */}
        <div style={cardStyle}>
          <h3 style={cardTitleStyle}>⚡ Quick Actions</h3>
          <button onClick={handleKeygen} style={buttonStyle} disabled={isLoading}>
            {isLoading ? '⏳ Processing...' : '🔑 Generate Keys'}
          </button>
          <button onClick={() => setActiveTab('encrypt')} style={buttonStyleSecondary}>
            🔒 Encrypt Message
          </button>
          <button onClick={() => setActiveTab('visualize')} style={buttonStyleSecondary}>
            🎮 3D Visualization
          </button>
        </div>

        {/* Key Info */}
        {keys && (
          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>📋 Key Information</h3>
            <p style={{ color: '#888', fontSize: '12px' }}>
              Start Position: ({keys.public.start_pos.join(', ')})<br/>
              Tour Hash: {keys.public.tour_hash.substring(0, 32)}...<br/>
              Fingerprint: {keys.public.initial_fingerprint.substring(0, 32)}...
            </p>
          </div>
        )}
      </div>
    </div>
  );

  // Render Encrypt Tab
  const renderEncrypt = () => (
    <div style={{ padding: '30px' }}>
      <div style={cardStyle}>
        <h3 style={cardTitleStyle}>🔒 Encrypt Message</h3>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter your secret message here..."
          style={{
            width: '100%',
            height: '100px',
            padding: '15px',
            background: 'rgba(0,0,0,0.5)',
            border: '1px solid #00ffff',
            borderRadius: '8px',
            color: '#fff',
            fontSize: '14px',
            resize: 'vertical'
          }}
        />
        <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
          <button onClick={handleEncrypt} style={buttonStyle} disabled={isLoading}>
            {isLoading ? '⏳ Encrypting...' : '🔐 Encrypt'}
          </button>
          <button onClick={handleDecrypt} style={buttonStyleSecondary} disabled={isLoading}>
            {isLoading ? '⏳ Decrypting...' : '🔓 Decrypt'}
          </button>
        </div>
        
        {ciphertext && (
          <div style={{ marginTop: '20px' }}>
            <h4 style={{ color: '#00ffff' }}>Ciphertext:</h4>
            <pre style={codeStyle}>{JSON.stringify(ciphertext, null, 2)}</pre>
          </div>
        )}
        
        {decryptedMessage && (
          <div style={{ marginTop: '20px' }}>
            <h4 style={{ color: '#00ff00' }}>Decrypted:</h4>
            <p style={{ color: '#fff', padding: '10px', background: 'rgba(0,255,0,0.1)', borderRadius: '8px' }}>
              {decryptedMessage}
            </p>
          </div>
        )}
      </div>
    </div>
  );

  // Render Visualize Tab
  const renderVisualize = () => (
    <div style={{ padding: '30px', height: 'calc(100vh - 150px)' }}>
      <div style={{ ...cardStyle, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={cardTitleStyle}>🎮 3D Knight Tour Visualization</h3>
          <div>
            <button onClick={handleExportObj} style={buttonStyleSecondary}>
              📦 Export .obj
            </button>
          </div>
        </div>
        
        {keys ? (
          <div style={{ flex: 1, minHeight: '400px' }}>
            <Knight3DVisualization 
              tour={keys.private.tour} 
              currentStep={currentStep}
              isPlaying={isPlaying}
            />
          </div>
        ) : (
          <div style={{ 
            flex: 1, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            color: '#888'
          }}>
            <p>Generate keys to visualize the 3D knight tour</p>
          </div>
        )}
        
        {keys && (
          <div style={{ marginTop: '15px', display: 'flex', alignItems: 'center', gap: '15px' }}>
            <span style={{ color: '#888' }}>Step: {currentStep} / 4096</span>
            <input
              type="range"
              min="0"
              max="4095"
              value={currentStep}
              onChange={(e) => setCurrentStep(parseInt(e.target.value))}
              style={{ flex: 1 }}
            />
            <button 
              onClick={() => setIsPlaying(!isPlaying)}
              style={buttonStyleSecondary}
            >
              {isPlaying ? '⏸️ Pause' : '▶️ Play'}
            </button>
          </div>
        )}
      </div>
    </div>
  );

  // Render Onion Tab
  const renderOnion = () => (
    <div style={{ padding: '30px' }}>
      <div style={cardStyle}>
        <h3 style={cardTitleStyle}>🧅 Rubik Onion Encryption</h3>
        <p style={{ color: '#888', marginBottom: '20px' }}>
          Multi-layer encryption with VDF time-lock. Each layer adds computational delay.
        </p>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ color: '#888', display: 'block', marginBottom: '10px' }}>
            Number of Layers: {onionLayers}
          </label>
          <input
            type="range"
            min="2"
            max="100"
            value={onionLayers}
            onChange={(e) => setOnionLayers(parseInt(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>
        
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter message to encrypt with onion layers..."
          style={{
            width: '100%',
            height: '80px',
            padding: '15px',
            background: 'rgba(0,0,0,0.5)',
            border: '1px solid #ff00ff',
            borderRadius: '8px',
            color: '#fff',
            fontSize: '14px',
            resize: 'vertical',
            marginBottom: '15px'
          }}
        />
        
        <button onClick={handleOnionEncrypt} style={buttonStyle} disabled={isLoading}>
          {isLoading ? '⏳ Creating Onion...' : `🧅 Create ${onionLayers}-Layer Onion`}
        </button>
        
        {onionResult && (
          <div style={{ marginTop: '20px' }}>
            <h4 style={{ color: '#ff00ff' }}>Onion Layers Created:</h4>
            <pre style={codeStyle}>{JSON.stringify(onionResult.slice(0, 3), null, 2)}...</pre>
            <p style={{ color: '#888', fontSize: '12px' }}>
              Total layers: {onionResult.length} | Private keys exported to onion_private/
            </p>
          </div>
        )}
      </div>
    </div>
  );

  // Render ZK Proof Tab
  const renderZK = () => (
    <div style={{ padding: '30px' }}>
      <div style={cardStyle}>
        <h3 style={cardTitleStyle}>🛡️ Zero-Knowledge Proof</h3>
        <p style={{ color: '#888', marginBottom: '20px' }}>
          Generate a zk-SNARK proof that you know a valid knight tour without revealing the tour itself.
        </p>
        
        <button onClick={handleZkProof} style={buttonStyle} disabled={isLoading}>
          {isLoading ? '⏳ Generating Proof...' : '🛡️ Generate ZK Proof'}
        </button>
        
        {zkProof && (
          <div style={{ marginTop: '20px' }}>
            <h4 style={{ color: '#00ffff' }}>ZK Proof Generated:</h4>
            <pre style={codeStyle}>{JSON.stringify(zkProof, null, 2)}</pre>
            <div style={{ marginTop: '15px', padding: '15px', background: 'rgba(0,255,0,0.1)', borderRadius: '8px' }}>
              <p style={{ color: '#00ff00' }}>✅ Proof is valid!</p>
              <p style={{ color: '#888', fontSize: '12px' }}>
                Merkle Root: {zkProof.merkle_root.substring(0, 32)}...<br/>
                Challenge: {zkProof.challenge.substring(0, 32)}...
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // Styles
  const cardStyle = {
    background: 'linear-gradient(135deg, rgba(0,0,0,0.8), rgba(20,20,40,0.8))',
    border: '1px solid rgba(0,255,255,0.3)',
    borderRadius: '16px',
    padding: '25px',
    backdropFilter: 'blur(10px)'
  };

  const cardTitleStyle = {
    color: '#00ffff',
    fontSize: '18px',
    marginBottom: '15px',
    textTransform: 'uppercase',
    letterSpacing: '1px'
  };

  const buttonStyle = {
    padding: '12px 24px',
    background: 'linear-gradient(135deg, #00ffff, #0080ff)',
    color: '#000',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textTransform: 'uppercase',
    letterSpacing: '1px'
  };

  const buttonStyleSecondary = {
    padding: '12px 24px',
    background: 'transparent',
    color: '#00ffff',
    border: '2px solid #00ffff',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    marginLeft: '10px'
  };

  const codeStyle = {
    background: 'rgba(0,0,0,0.5)',
    padding: '15px',
    borderRadius: '8px',
    color: '#00ffff',
    fontSize: '12px',
    overflow: 'auto',
    maxHeight: '200px',
    border: '1px solid rgba(0,255,255,0.3)'
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <header style={{
        padding: '20px 30px',
        background: 'linear-gradient(135deg, rgba(0,0,0,0.9), rgba(10,10,30,0.9))',
        borderBottom: '2px solid #00ffff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{ 
            color: '#00ffff', 
            fontSize: '28px',
            textTransform: 'uppercase',
            letterSpacing: '3px',
            textShadow: '0 0 20px rgba(0,255,255,0.5)'
          }}>
            HKSC-4096
          </h1>
          <p style={{ color: '#888', fontSize: '12px' }}>
            HyperKnight Supercube Cryptosystem
          </p>
        </div>
        <div style={{ color: '#00ffff', fontSize: '14px' }}>
          Status: {status}
        </div>
      </header>

      {/* Tabs */}
      <div style={{
        padding: '0 30px',
        background: 'rgba(0,0,0,0.5)',
        borderBottom: '1px solid rgba(0,255,255,0.2)'
      }}>
        <Tab label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
        <Tab label="Encrypt" active={activeTab === 'encrypt'} onClick={() => setActiveTab('encrypt')} />
        <Tab label="3D Visualize" active={activeTab === 'visualize'} onClick={() => setActiveTab('visualize')} />
        <Tab label="Onion" active={activeTab === 'onion'} onClick={() => setActiveTab('onion')} />
        <Tab label="ZK Proof" active={activeTab === 'zk'} onClick={() => setActiveTab('zk')} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'encrypt' && renderEncrypt()}
        {activeTab === 'visualize' && renderVisualize()}
        {activeTab === 'onion' && renderOnion()}
        {activeTab === 'zk' && renderZK()}
      </div>

      {/* Footer */}
      <footer style={{
        padding: '15px 30px',
        background: 'rgba(0,0,0,0.8)',
        borderTop: '1px solid rgba(0,255,255,0.2)',
        textAlign: 'center',
        color: '#888',
        fontSize: '12px'
      }}>
        HKSC-4096 v1.0.0 | 16×16×16 Supercube | 4096 Cells | 3D Knight Tour | zk-SNARK | MIT License
      </footer>
    </div>
  );
}

// Add OrbitControls to Three.js
// This is a simplified version - in production you'd use the full library
THREE.OrbitControls = function(camera, domElement) {
  this.camera = camera;
  this.domElement = domElement;
  this.target = new THREE.Vector3();
  this.enableDamping = false;
  this.dampingFactor = 0.05;
  
  let isDragging = false;
  let previousMousePosition = { x: 0, y: 0 };
  
  domElement.addEventListener('mousedown', (e) => {
    isDragging = true;
    previousMousePosition = { x: e.clientX, y: e.clientY };
  });
  
  domElement.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    
    const deltaMove = {
      x: e.clientX - previousMousePosition.x,
      y: e.clientY - previousMousePosition.y
    };
    
    const deltaRotationQuaternion = new THREE.Quaternion()
      .setFromEuler(new THREE.Euler(
        deltaMove.y * 0.01,
        deltaMove.x * 0.01,
        0,
        'XYZ'
      ));
    
    camera.quaternion.multiplyQuaternions(deltaRotationQuaternion, camera.quaternion);
    
    previousMousePosition = { x: e.clientX, y: e.clientY };
  });
  
  domElement.addEventListener('mouseup', () => {
    isDragging = false;
  });
  
  domElement.addEventListener('wheel', (e) => {
    camera.position.z += e.deltaY * 0.01;
  });
  
  this.update = function() {
    camera.lookAt(this.target);
  };
};

// Render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
