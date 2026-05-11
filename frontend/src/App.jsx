import { Routes, Route } from 'react-router-dom';
import { Landing } from './components/Landing';
import { PredictorLayout } from './components/predictor/PredictorLayout';
import { SimulatorLayout } from './components/simulator/SimulatorLayout';
import { CollegesList } from './components/colleges/CollegesList';
import { CollegeDetail } from './components/colleges/CollegeDetail';

function App() {
  return (
    <div className="min-h-screen">
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/predictor" element={<PredictorLayout />} />
        <Route path="/simulator" element={<SimulatorLayout />} />
        <Route path="/colleges" element={<CollegesList />} />
        <Route path="/colleges/:code" element={<CollegeDetail />} />
      </Routes>
    </div>
  );
}

export default App;
