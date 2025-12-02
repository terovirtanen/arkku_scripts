
<?php
// API endpoint to record pellet scale weight and get summary from database
// http post to record, body
// mandatory: weight=1234.25
// optional : type=init
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

// Handle POST request - record weight
function handlePostRequest($db) {
    // Get POST data
    $input = json_decode(file_get_contents('php://input'), true);
    
    // Check for weight in POST body or fallback to POST parameters
    $weight = null;
    if (isset($input['weight'])) {
        $weight = floatval($input['weight']);
    } elseif (isset($_POST['weight'])) {
        $weight = floatval($_POST['weight']);
    }
    
    if ($weight === null) {
        http_response_code(400);
        echo json_encode(['error' => 'Weight parameter is required']);
        return;
    }
    
    $type = $input['type'] ?? $_POST['type'] ?? 'reading';
    
    try {
        $id = $db->insertWeightReading($weight, $type);
        echo json_encode([
            'success' => true,
            'message' => 'Weight recorded successfully',
            'data' => [
                'id' => $id,
                'weight' => $weight,
                'type' => $type,
                'timestamp' => date('Y-m-d H:i:s')
            ]
        ]);
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to record weight']);
    }
}

// Handle GET request - get summary
function handleGetRequest($db) {
    $timePeriod = $_GET['timeperiod'] ?? 'week';
    
    // Validate time period
    $validPeriods = ['day', 'week', 'month', 'year'];
    if (!in_array($timePeriod, $validPeriods)) {
        $timePeriod = 'week';
    }
    
    try {
        $summary = $db->getSummary($timePeriod);
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
    case 'POST':
        handlePostRequest($db);
        break;
    case 'GET':
        handleGetRequest($db);
        break;
    default:
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed. Use POST to record weight or GET to get summary']);
        break;
}
?>

