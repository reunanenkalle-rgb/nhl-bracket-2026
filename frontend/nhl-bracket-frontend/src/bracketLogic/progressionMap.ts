// frontend/src/bracketLogic/progressionMap.ts

// Defines which series' winner populates which slot in the next round's series
// Key: series_identifier of the series whose winner is advancing
// Value: { nextSeriesId: series_identifier of the series they advance to,
//          slot: 'team1' or 'team2' indicating which position they take }
export const progressionMap: Record<string, { nextSeriesId: string; slot: 'team1' | 'team2' }> = {
    // Eastern Conference
    'EC_R1_M1': { nextSeriesId: 'EC_R2_M1', slot: 'team1' },
    'EC_R1_M2': { nextSeriesId: 'EC_R2_M1', slot: 'team2' },
    'EC_R1_M3': { nextSeriesId: 'EC_R2_M2', slot: 'team1' },
    'EC_R1_M4': { nextSeriesId: 'EC_R2_M2', slot: 'team2' },
  
    'EC_R2_M1': { nextSeriesId: 'EC_R3_CF', slot: 'team1' },
    'EC_R2_M2': { nextSeriesId: 'EC_R3_CF', slot: 'team2' },
  
    'EC_R3_CF': { nextSeriesId: 'SCF', slot: 'team1' },
  
    // Western Conference
    'WC_R1_M1': { nextSeriesId: 'WC_R2_M1', slot: 'team1' },
    'WC_R1_M2': { nextSeriesId: 'WC_R2_M1', slot: 'team2' },
    'WC_R1_M3': { nextSeriesId: 'WC_R2_M2', slot: 'team1' },
    'WC_R1_M4': { nextSeriesId: 'WC_R2_M2', slot: 'team2' },
  
    'WC_R2_M1': { nextSeriesId: 'WC_R3_CF', slot: 'team1' },
    'WC_R2_M2': { nextSeriesId: 'WC_R3_CF', slot: 'team2' },
  
    'WC_R3_CF': { nextSeriesId: 'SCF', slot: 'team2' },
  };