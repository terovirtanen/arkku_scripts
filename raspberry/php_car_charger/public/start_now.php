<?php
// API endpoint to start car charging for 1, 2 or 3 hours from now
// http get, query parameters:
// optional : hours=<1|2|3> (default 1)
// optional : power_charging=<true|false> (default false), false -> period_type solar (10A), true -> solar_max (16A)

$timezone = "Europe/Helsinki";
date_default_timezone_set($timezone);

header('Content-Type: application/json');

require_once __DIR__ . '/../config/database.php';

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed. Use GET']);
    exit;
}

$db = null;
try {
    $db = Database::getInstance();
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

$hours = $_GET['hours'] ?? 1;
$powerCharging = filter_var($_GET['power_charging'] ?? false, FILTER_VALIDATE_BOOLEAN);

if (!in_array((string)$hours, ['1', '2', '3'], true)) {
    http_response_code(400);
    echo json_encode(['error' => 'hours must be 1, 2 or 3']);
    exit;
}

$hours = (int)$hours;
$periodType = $powerCharging ? 'solar_max' : 'solar';

$start = new DateTime('now');
$start->setTime((int)$start->format('H'), (int)$start->format('i'), 0);
$end = (clone $start)->modify("+{$hours} hours");

try {
    $id = $db->insertChargingPeriod($start->format('Y-m-d H:i:s'), $end->format('Y-m-d H:i:s'), $periodType);
    echo json_encode([
        'success' => true,
        'message' => 'Charging period added',
        'data' => [
            'id' => $id,
            'start_time' => $start->format('Y-m-d H:i:s'),
            'end_time' => $end->format('Y-m-d H:i:s'),
            'hours' => $hours,
            'period_type' => $periodType
        ]
    ]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to add charging period']);
}
?>
