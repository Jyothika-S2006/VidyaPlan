import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import DataPage from './pages/DataPage'
import BudgetPage from './pages/BudgetPage'
import PlanPage from './pages/PlanPage'
import ReviewPage from './pages/ReviewPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/data" replace />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/budget" element={<BudgetPage />} />
        <Route path="/plan" element={<PlanPage />} />
        <Route path="/review" element={<ReviewPage />} />
      </Route>
    </Routes>
  )
}
