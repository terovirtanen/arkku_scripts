<?php
$timezone = "Europe/Helsinki";

date_default_timezone_set($timezone);

$jsonRaw = file_get_contents('https://api.porssisahko.net/v2/latest-prices.json');
$jsonData = json_decode($jsonRaw, true);

$formattedData = [];

// Get today's and tomorrow's dates
$hour_current = date("G");

// Get the requested date from the query parameter
$requestDate = $_GET['date'] ?? 'today'; // Default to 'today' if no parameter is provided
$requestHour = $_GET['hour'] ?? $hour_current; // Default to current hour if no parameter is provided

$today = date("Y-n-j G", strtotime("today $requestHour:00"));
$tomorrow = date("Y-n-j G", strtotime("tomorrow $requestHour:00"));

if ($requestDate === 'today') {
    $filterDate = $today;
} elseif ($requestDate === 'tomorrow') {
    $filterDate = $tomorrow;
} else {
    // Invalid date parameter, return an error
    header("Content-Type: application/json");
    echo json_encode(["error" => "Invalid date parameter. Use 'today' or 'tomorrow'."]);
    exit;
}

// Initialize the array with 4 null values for the requested date hour quater
$formattedData[$filterDate] = array_fill(0, 4, null);

foreach ($jsonData['prices'] as $entry) {
    $date = date("Y-n-j", strtotime($entry['startDate'])); // Format date as "YYYY-M-D"
    $hour = (int)date("G", strtotime($entry['startDate'])); // Get the hour (0-23)
    $minute = (int)date("i", strtotime($entry['startDate'])); // Get the minute (0-59)
    $quarter = (int)($minute / 15); // Get the quarter-hour index (0-3)
    $price = (int)$entry['price']; // Convert price to integer

    // Only include data for the requested date
    if ($date !== $filterDate) {
        continue;
    }
    if ($hour !== (int)$requestHour) {
        continue;
    }

    // Set the price at the correct quarter index
    $formattedData[$filterDate][$quarter] = $price;
}

header("Content-Type: application/json");
echo json_encode($formattedData);
?>

