import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import 'bootstrap/dist/css/bootstrap.css';
import Home from './pages/Home';
import './App.css';

function App() {
  return (
    <div data-bs-theme="dark">
    <Router>
      <Routes>
        {/*Public Routes*/}
        <Route path="/" element={<Home />} />

      </Routes>
    </Router>
    </div>
  );
}

export default App;
