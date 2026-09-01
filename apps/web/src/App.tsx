import { Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AccountPage } from "./pages/AccountPage";
import { ArticlePage } from "./pages/ArticlePage";
import { AuthorityDashboardPage } from "./pages/AuthorityDashboardPage";
import { AuthorityPetitionsPage } from "./pages/AuthorityPetitionsPage";
import { AuthorityReportPage } from "./pages/AuthorityReportPage";
import { CreatePetitionPage } from "./pages/CreatePetitionPage";
import { DocumentBrowserPage } from "./pages/DocumentBrowserPage";
import { HomePage } from "./pages/HomePage";
import { LearnPage } from "./pages/LearnPage";
import { LegalAssistantPage } from "./pages/LegalAssistantPage";
import { LoginPage } from "./pages/LoginPage";
import { MyPetitionsPage } from "./pages/MyPetitionsPage";
import { MyReportsPage } from "./pages/MyReportsPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PetitionDetailPage } from "./pages/PetitionDetailPage";
import { PetitionsPage } from "./pages/PetitionsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ReportDetailPage } from "./pages/ReportDetailPage";
import { ReportPage } from "./pages/ReportPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/learn" element={<LearnPage />} />
        <Route path="/learn/browse" element={<DocumentBrowserPage />} />
        <Route path="/learn/:slug" element={<ArticlePage />} />
        {/* Public by standing decision: basic legal information must not require an account. */}
        <Route path="/legal-assistant" element={<LegalAssistantPage />} />
        <Route
          path="/account"
          element={
            <ProtectedRoute>
              <AccountPage />
            </ProtectedRoute>
          }
        />
        {/* Civic reporting is tied to an account: a report has an owner.
            Citizen-only to match the API — staff process reports rather
            than filing them, and offering them the form would only 403. */}
        <Route
          path="/report"
          element={
            <ProtectedRoute roles={["CITIZEN"]}>
              <ReportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports/mine"
          element={
            <ProtectedRoute>
              <MyReportsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports/:id"
          element={
            <ProtectedRoute>
              <ReportDetailPage />
            </ProtectedRoute>
          }
        />
        {/* Authority workspace. The role check here hides the UI; the API
            independently authorises every action behind it. */}
        <Route
          path="/authority"
          element={
            <ProtectedRoute roles={["AUTHORITY", "ADMIN"]}>
              <AuthorityDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/authority/reports/:id"
          element={
            <ProtectedRoute roles={["AUTHORITY", "ADMIN"]}>
              <AuthorityReportPage />
            </ProtectedRoute>
          }
        />
        {/* Petitions are public content: reading one needs no account,
            matching the API. Publishing, signing and moderating do. */}
        <Route path="/petitions" element={<PetitionsPage />} />
        <Route
          path="/petitions/new"
          element={
            <ProtectedRoute roles={["CITIZEN"]}>
              <CreatePetitionPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/petitions/mine"
          element={
            <ProtectedRoute>
              <MyPetitionsPage />
            </ProtectedRoute>
          }
        />
        <Route path="/petitions/:id" element={<PetitionDetailPage />} />
        <Route
          path="/authority/petitions"
          element={
            <ProtectedRoute roles={["AUTHORITY", "ADMIN"]}>
              <AuthorityPetitionsPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  );
}
