import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Pagination
} from '@mui/material';
import { Search, Clear } from '@mui/icons-material';

import apiService from '../services/apiService';
import { PolicySearchCriteria, PolicySearchResult } from '../types';

const PolicySearchPage: React.FC = () => {
  const [searchCriteria, setSearchCriteria] = useState<PolicySearchCriteria>({
    search_type: 'partial',
    page: 1,
    page_size: 25
  });

  const [hasSearched, setHasSearched] = useState(false);

  const {
    data: searchResults,
    isLoading,
    error,
    refetch
  } = useQuery<PolicySearchResult>({
    queryKey: ['policySearch', searchCriteria],
    queryFn: () => apiService.searchPolicies(searchCriteria),
    enabled: hasSearched
  });

  const handleInputChange = (field: keyof PolicySearchCriteria, value: any) => {
    setSearchCriteria(prev => ({
      ...prev,
      [field]: value,
      page: 1 // Reset to first page when search criteria changes
    }));
  };

  const handleSearch = () => {
    setHasSearched(true);
    refetch();
  };

  const handleReset = async () => {
    try {
      const response = await apiService.resetSearchCriteria();
      setSearchCriteria({
        ...response.default_criteria,
        search_type: 'partial',
        page: 1,
        page_size: 25
      });
      setHasSearched(false);
    } catch (error) {
      console.error('Failed to reset search criteria:', error);
    }
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setSearchCriteria(prev => ({ ...prev, page }));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Policy Search
      </Typography>

      {/* Search Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Policy Number"
                value={searchCriteria.policy_number || ''}
                onChange={(e) => handleInputChange('policy_number', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Insured First Name"
                value={searchCriteria.insured_first_name || ''}
                onChange={(e) => handleInputChange('insured_first_name', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Insured Last Name"
                value={searchCriteria.insured_last_name || ''}
                onChange={(e) => handleInputChange('insured_last_name', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Organization Name"
                value={searchCriteria.organization_name || ''}
                onChange={(e) => handleInputChange('organization_name', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="City"
                value={searchCriteria.policy_city || ''}
                onChange={(e) => handleInputChange('policy_city', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="State"
                value={searchCriteria.policy_state || ''}
                onChange={(e) => handleInputChange('policy_state', e.target.value)}
                inputProps={{ maxLength: 2 }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="ZIP Code"
                value={searchCriteria.policy_zip || ''}
                onChange={(e) => handleInputChange('policy_zip', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Search Type</InputLabel>
                <Select
                  value={searchCriteria.search_type}
                  onChange={(e) => handleInputChange('search_type', e.target.value)}
                >
                  <MenuItem value="exact">Exact Match</MenuItem>
                  <MenuItem value="partial">Partial Match</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="SSN/TIN (Last 4 digits)"
                value={searchCriteria.ssn_tin || ''}
                onChange={(e) => handleInputChange('ssn_tin', e.target.value)}
                inputProps={{ maxLength: 4 }}
                helperText="Enter last 4 digits for secure search"
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<Search />}
                  onClick={handleSearch}
                  disabled={isLoading}
                >
                  Search Policies
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Clear />}
                  onClick={handleReset}
                >
                  Reset
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Search Results */}
      {hasSearched && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Search Results
              {searchResults && ` (${searchResults.total} found)`}
            </Typography>

            {isLoading && (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            )}

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Search failed. Please try again.
              </Alert>
            )}

            {searchResults && searchResults.policies.length === 0 && (
              <Alert severity="info">
                No matching policies found.
              </Alert>
            )}

            {searchResults && searchResults.policies.length > 0 && (
              <>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Policy Number</TableCell>
                        <TableCell>Insured Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Effective Date</TableCell>
                        <TableCell>Location</TableCell>
                        <TableCell>Active</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {searchResults.policies.map((policy) => (
                        <TableRow key={policy.id} hover>
                          <TableCell>
                            <Button
                              variant="text"
                              color="primary"
                              href={`/policies/${policy.id}`}
                            >
                              {policy.policy_number}
                            </Button>
                          </TableCell>
                          <TableCell>{policy.insured_full_name}</TableCell>
                          <TableCell>
                            <Chip label={policy.policy_type} size="small" />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={policy.status}
                              color={policy.is_active ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{policy.effective_date}</TableCell>
                          <TableCell>{policy.city}, {policy.state}</TableCell>
                          <TableCell>
                            <Chip
                              label={policy.is_active ? 'Yes' : 'No'}
                              color={policy.is_active ? 'success' : 'error'}
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Pagination
                    count={searchResults.total_pages}
                    page={searchResults.page}
                    onChange={handlePageChange}
                    color="primary"
                  />
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PolicySearchPage;