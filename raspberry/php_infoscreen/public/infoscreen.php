
<?php
// API endpoint to get data to infoscreen from database
// http get to get summary, parameters
// optional (default is week) : timeperiod=<day|week|month|year>

$timezone = "Europe/Helsinki";
date_default_timezone_set($timezone);

header('Content-Type: application/json');

require_once __DIR__ . '/../config/database.php';

// Initialize database connection
$db = null;
try {
    $db = Database::getInstance();
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// Handle GET request - get porssisahko next hours data
function handleGetRequest($db) {
    $porssisahkoTimePeriod = $_GET['porssisahko'] ?? '4h';
    
    // Validate time period
    $validPeriods = ['2h', '4h', '6h', '8h'];
    if (!in_array($porssisahkoTimePeriod, $validPeriods)) {
        $porssisahkoTimePeriod = '4h';
    }
    
    try {
        $summary = $db->getPorssisahkoData($porssisahkoTimePeriod);
        echo json_encode([
            'success' => true,
            'data' => $summary
        ]);
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to get summary']);
    }
}

// Route requests based on HTTP method
switch ($_SERVER['REQUEST_METHOD']) {
    case 'GET':
        handleGetRequest($db);
        break;
    default:
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed. Use GET to get porssisahko summary']);
        break;
}
?>

