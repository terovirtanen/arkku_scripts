<?php
class Database {
    private static $instance = null;
    private $connection;

    private function __construct() {
        $dsn = "mysql:host=" . ($_ENV['DB_HOST'] ?? 'localhost')
            . ";port=" . ($_ENV['DB_PORT'] ?? 3306)
            . ";dbname=" . ($_ENV['DB_NAME'] ?? 'porssisahkonet')
            . ";charset=utf8mb4";

        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::MYSQL_ATTR_SSL_VERIFY_SERVER_CERT => false,
        ];

        try {
            $this->connection = new PDO($dsn, $_ENV['DB_USER'], $_ENV['DB_PASSWORD'], $options);
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            throw new Exception("Database connection failed");
        }
    }

    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    // table car_charger is created by porssisahko_optimize_charging.py
    public function insertChargingPeriod($startTime, $endTime, $periodType) {
        $stmt = $this->connection->prepare(
            "INSERT INTO car_charger (start_time, end_time, average_price, period_type) VALUES (?, ?, 0, ?)"
        );
        $stmt->execute([$startTime, $endTime, $periodType]);
        return (int)$this->connection->lastInsertId();
    }
}
?>
