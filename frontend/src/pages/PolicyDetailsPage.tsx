import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, CircularProgress } from '@mui/material';

const PolicyDetailsPage: React.FC = () => {
  const { policyId } = useParams<{ policyId: string }>();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Policy Details
      </Typography>
      <Typography>
        Policy ID: {policyId}
      </Typography>
      <Typography color="text.secondary">
        Policy details implementation in progress...
      </Typography>
    </Box>
  );
};

export default PolicyDetailsPage;