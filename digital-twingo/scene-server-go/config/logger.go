package config

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
)

var LogWriter io.Writer

func InitLogger(logPath string) error {
	if err := os.MkdirAll(filepath.Dir(logPath), 0755); err != nil {
		return err
	}
	f, err := os.OpenFile(logPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	LogWriter = f
	// Also write Gin debug output to log file
	gin.DefaultWriter = io.MultiWriter(os.Stdout, f)
	gin.DefaultErrorWriter = io.MultiWriter(os.Stderr, f)
	return nil
}

func Log(level, format string, args ...interface{}) {
	msg := fmt.Sprintf(format, args...)
	line := fmt.Sprintf("[%s] %-5s %s\n", time.Now().Format("2006-01-02 15:04:05"), level, msg)
	if LogWriter != nil {
		LogWriter.Write([]byte(line))
	}
	fmt.Print(line)
}

func RequestLogger() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()
		duration := time.Since(start)
		Log("INFO", "%s %s %d %v",
			c.Request.Method,
			c.Request.URL.String(),
			c.Writer.Status(),
			duration.Round(time.Millisecond),
		)
	}
}
