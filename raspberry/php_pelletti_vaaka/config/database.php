<?php
class Database {
    private static $instance = null;
    private $connection;
    
    private function __construct() {
        $config = [
            'host' => $_ENV['DB_HOST'] ?? 'localhost',
            'dbname' => $_ENV['DB_NAME'],
            'username' => $_ENV['DB_USER'],
            'password' => $_ENV['DB_PASSWORD'],
        ];
        
        $dsn = "mysql:host={$config['host']};dbname={$config['dbname']};charset=utf8mb4";
        
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::MYSQL_ATTR_SSL_VERIFY_SERVER_CERT => false,
        ];
        
        try {
            $this->connection = new PDO($dsn, $config['username'], $config['password'], $options);
        } catch (PDOException $e) {
            $this->createDatabaseIfNotExists();
            try {
                $this->connection = new PDO($dsn, $config['username'], $config['password'], $options);
            } catch (PDOException $e) {
                error_log("Database connection failed: " . $e->getMessage());
                throw new Exception("Database connection failed");
            }
        }
    }
    
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    public function getConnection() {
        return $this->connection;
    }

    // create database if it does not exist
    // database columns are
    // id (int, primary key, auto increment)
    // weight (float)
    // time (datetime)
    // type (varchar 50)
    private function createDatabaseIfNotExists() {
        $config = [
            'host' => $_ENV['DB_HOST'] ?? 'localhost',
            'username' => $_ENV['DB_USER'],
            'password' => $_ENV['DB_PASSWORD'],
            'dbname' => $_ENV['DB_NAME']
        ];
        
        try {
            // Connect without specifying database
            $dsn = "mysql:host={$config['host']};charset=utf8mb4";
            $tempPdo = new PDO($dsn, $config['username'], $config['password'], [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
            ]);
            
            // Create database if it doesn't exist
            $stmt = $tempPdo->prepare("CREATE DATABASE IF NOT EXISTS `{$config['dbname']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
            $stmt->execute();
            
            // Connect to the created database
            $dsn = "mysql:host={$config['host']};dbname={$config['dbname']};charset=utf8mb4";
            $dbPdo = new PDO($dsn, $config['username'], $config['password'], [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
            ]);
            
            // Create table if it doesn't exist
            $createTableSql = "
                CREATE TABLE IF NOT EXISTS pellet_measurements (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    weight FLOAT NOT NULL,
                    time DATETIME NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    INDEX idx_time (time),
                    INDEX idx_type (type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ";
            
            $stmt = $dbPdo->prepare($createTableSql);
            $stmt->execute();
            
            error_log("Database '{$config['dbname']}' and table 'pellet_measurements' created or already exist");
        } catch (PDOException $e) {
            error_log("Failed to create database or table: " . $e->getMessage());
            throw new Exception("Failed to create database or table");
        }
    }
    
    public function insertWeightReading($weight, $type = 'reading') {
        try {
            $stmt = $this->connection->prepare("INSERT INTO pellet_measurements (weight, time, type) VALUES (:weight, NOW(), :type)");
            $stmt->bindParam(':weight', $weight, PDO::PARAM_STR);
            $stmt->bindParam(':type', $type, PDO::PARAM_STR);
            $stmt->execute();
            return $this->connection->lastInsertId();
        } catch (PDOException $e) {
            error_log("Failed to insert weight reading: " . $e->getMessage());
            throw new Exception("Failed to record weight");
        }
    }
    
    public function getSummary($timePeriod = 'week') {
        $whereClause = $this->getTimeWhereClause($timePeriod);
        
        try {
            // Get summary statistics
            $stmt = $this->connection->prepare("
                SELECT 
                    COUNT(*) as reading_count,
                    AVG(weight) as avg_weight,
                    MIN(weight) as min_weight,
                    MAX(weight) as max_weight,
                    MAX(time) as latest_reading,
                    MIN(time) as first_reading
                FROM pellet_measurements 
                WHERE $whereClause
            ");
            $stmt->execute();
            $summary = $stmt->fetch();
            
            // Get weight change (difference between first and last reading)
            $stmt = $this->connection->prepare("
                SELECT 
                    (SELECT weight FROM pellet_measurements WHERE $whereClause ORDER BY time DESC LIMIT 1) - 
                    (SELECT weight FROM pellet_measurements WHERE $whereClause ORDER BY time ASC LIMIT 1) as weight_change
            ");
            $stmt->execute();
            $change = $stmt->fetch();
            
            $summary['weight_change'] = $change['weight_change'];
            $summary['time_period'] = $timePeriod;
            
            return $summary;
        } catch (PDOException $e) {
            error_log("Failed to get summary: " . $e->getMessage());
            throw new Exception("Failed to get summary");
        }
    }
    
    private function getTimeWhereClause($timePeriod) {
        switch ($timePeriod) {
            case 'day':
                return "time >= DATE_SUB(NOW(), INTERVAL 1 DAY)";
            case 'week':
                return "time >= DATE_SUB(NOW(), INTERVAL 1 WEEK)";
            case 'month':
                return "time >= DATE_SUB(NOW(), INTERVAL 1 MONTH)";
            case 'year':
                return "time >= DATE_SUB(NOW(), INTERVAL 1 YEAR)";
            default:
                return "time >= DATE_SUB(NOW(), INTERVAL 1 WEEK)"; // default to week
        }
    }
}

// Käyttö
try {
    $db = Database::getInstance();
    $db->createDatabaseIfNotExists();
    $pdo = $db->getConnection();
} catch (Exception $e) {
    die("Database error occurred");
}
?>