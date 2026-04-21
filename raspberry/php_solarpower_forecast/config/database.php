<?php
// MySQLi connection for Forecast.php compatibility

$dbHost = $_ENV['DB_HOST'] ?? 'localhost';
$dbUser = $_ENV['DB_USER'];
$dbPassword = $_ENV['DB_PASSWORD'];
$dbName = $_ENV['DB_NAME'];
$dbPort = isset($_ENV['DB_PORT']) ? (int)$_ENV['DB_PORT'] : 3306;

// Create database if it does not exist
$tempConn = new mysqli($dbHost, $dbUser, $dbPassword, '', $dbPort);
if ($tempConn->connect_error) {
    http_response_code(500);
    die("Database connection failed: " . $tempConn->connect_error);
}
$tempConn->query("CREATE DATABASE IF NOT EXISTS `{$dbName}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
$tempConn->close();

$conn = new mysqli($dbHost, $dbUser, $dbPassword, $dbName, $dbPort);
if ($conn->connect_error) {
    http_response_code(500);
    die("Database connection failed: " . $conn->connect_error);
}
$conn->set_charset('utf8mb4');

// Create table if it does not exist
$conn->query("
    CREATE TABLE IF NOT EXISTS forecast_fmi_daily (
        id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        date DATETIME NOT NULL UNIQUE,
        clouds INT,
        maxpower INT NOT NULL,
        forecastpower INT NOT NULL,
        weathersymbol INT,
        INDEX idx_date (date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
");
