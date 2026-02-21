import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, Button, Container } from '@mui/material';

// Page components
import PolicySearchPage from './pages/PolicySearchPage';
import PolicyDetailsPage from './pages/PolicyDetailsPage';
import ClaimsPage from './pages/ClaimsPage';
import PaymentsPage from './pages/PaymentsPage';

// Create MUI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Box sx={{ flexGrow: 1 }}>
            <AppBar position="static">
              <Toolbar>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                  Claims Service Platform
                </Typography>
                <Button color="inherit" href="/policies/search">
                  Policies
                </Button>
                <Button color="inherit" href="/claims">
                  Claims
                </Button>
                <Button color="inherit" href="/payments">
                  Payments
                </Button>
              </Toolbar>
            </AppBar>

            <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
              <Routes>
                <Route path="/" element={<Navigate to="/policies/search" replace />} />
                <Route path="/policies/search" element={<PolicySearchPage />} />
                <Route path="/policies/:policyId" element={<PolicyDetailsPage />} />
                <Route path="/claims" element={<ClaimsPage />} />
                <Route path="/payments" element={<PaymentsPage />} />
              </Routes>
            </Container>
          </Box>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;