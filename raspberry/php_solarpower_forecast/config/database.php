<?php
// MySQLi connection for Forecast.php compatibility

$conn = new mysqli(
    $_ENV['DB_HOST'] ?? 'localhost',
    $_ENV['DB_USER'],
    $_ENV['DB_PASSWORD'],
    $_ENV['DB_NAME'],
    isset($_ENV['DB_PORT']) ? (int)$_ENV['DB_PORT'] : 3306
);

if ($conn->connect_error) {
    http_response_code(500);
    die("Database connection failed: " . $conn->connect_error);
}

$conn->set_charset('utf8mb4');
