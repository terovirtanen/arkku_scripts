<?php
date_default_timezone_set($timezone);

$jsonRaw = file_get_contents('https://api.porssisahko.net/v1/latest-prices.json');
$jsonData = json_decode($jsonRaw, true);

$formattedData = [];

// Get today's and tomorrow's dates
$today = date("Y-n-j");
$tomorrow = date("Y-n-j", strtotime("+1 day"));

// Get the requested date from the query parameter
$requestDate = $_GET['date'] ?? 'today'; // Default to 'today' if no parameter is provided

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

// Initialize the array with 24 null values for the requested date
$formattedData[$filterDate] = array_fill(0, 24, null);

foreach ($jsonData['prices'] as $entry) {
    $date = date("Y-n-j", strtotime($entry['startDate'])); // Format date as "YYYY-M-D"
    $hour = (int)date("G", strtotime($entry['startDate'])); // Get the hour (0-23)
    $price = (int)$entry['price']; // Convert price to integer

    // Only include data for the requested date
    if ($date !== $filterDate) {
        continue;
    }

    // Set the price at the correct hour index
    $formattedData[$filterDate][$hour] = $price;
}

header("Content-Type: application/json");
echo json_encode($formattedData);
?>

