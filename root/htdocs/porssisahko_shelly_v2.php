<?php
$timezone = "Europe/Helsinki";

date_default_timezone_set($timezone);

$jsonRaw = file_get_contents('https://api.porssisahko.net/v2/latest-prices.json');
$jsonData = json_decode($jsonRaw, true);

$formattedData = [];

# output example
# {"2025-10-3":{"1":[0,0,0,0],"0":[0,0,0,0]},"2025-10-2":{"23":[1,1,0,0],"22":[2,2,1,1],"21":[4,2,1,1],"20":[11,9,7,5],"19":[21,21,13,10],"18":[24,22,22,14]}}

$fDates = [];
$h = 0;
while ($h < 8) {
    $fDates[date("Y-n-j", strtotime("+".$h." hour"))][date("G", strtotime("+".$h." hour"))] = null;
    $h++;
}


foreach ($jsonData['prices'] as $entry) {
    $date = date("Y-n-j", strtotime($entry['startDate'])); // Format date as "YYYY-M-D"
    $hour = (int)date("G", strtotime($entry['startDate'])); // Get the hour (0-23)
    $minute = (int)date("i", strtotime($entry['startDate'])); // Get the minute (0-59)
    $quarter = (int)($minute / 15); // Get the quarter-hour index (0-3)
    $price = (int)$entry['price']; // Convert price to integer
    
    // Only include data for the requested date
    if (!isset($fDates[$date]) || !array_key_exists($hour, $fDates[$date])) {
        continue;
    }
    
    if (!isset($formattedData[$date])) {
        $formattedData[$date] = [];
    }
    if (!isset($formattedData[$date][$hour])) {
        // Initialize the array with 4 null values for the requested date hour quater
        $formattedData[$date][$hour] = array_fill(0, 4, null);
    }
    $formattedData[$date][$hour][$quarter] = $price;
}

header("Content-Type: application/json");
echo json_encode($formattedData);
?>

