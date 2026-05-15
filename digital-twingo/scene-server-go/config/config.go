package config

import (
	"os"
	"strconv"
	"strings"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Server  ServerConfig  `yaml:"server"`
	Spring  SpringConfig  `yaml:"spring"`
	Mybatis MybatisConfig `yaml:"mybatis"`
	Swagger SwaggerConf   `yaml:"swagger"`
	Iot     IotConfig     `yaml:"iot"`
	LLM     LLMConfig     `yaml:"llm"`
	RAG     RAGConfig     `yaml:"rag"`
}

type ServerConfig struct {
	Port    string        `yaml:"port"`
	Servlet ServletConfig `yaml:"servlet"`
}

type ServletConfig struct {
	ContextPath string `yaml:"context-path"`
}

type SpringConfig struct {
	Datasource DatasourceConfig `yaml:"datasource"`
}

type DatasourceConfig struct {
	DriverClass string `yaml:"driver-class-name"`
	URL         string `yaml:"url"`
	Username    string `yaml:"username"`
	Password    string `yaml:"password"`
}

type MybatisConfig struct {
	MapperLocations string `yaml:"mapper-locations"`
	ConfigLocation  string `yaml:"config-location"`
}

type SwaggerConf struct {
	Enable bool `yaml:"enable"`
}

type IotConfig struct {
	MqttBroker       string `yaml:"mqtt-broker"`
	MqttClientId     string `yaml:"mqtt-client-id"`
	SimulatorEnabled bool   `yaml:"simulator-enabled"`
}

type LLMConfig struct {
	Enabled        bool   `yaml:"enabled"`
	BaseURL        string `yaml:"base-url"`
	APIKey         string `yaml:"api-key"`
	Model          string `yaml:"model"`
	TimeoutSeconds int    `yaml:"timeout-seconds"`
	MaxToolRounds  int    `yaml:"max-tool-rounds"`
}

type RAGConfig struct {
	Enabled bool `yaml:"enabled"`
}

var AppConfig *Config

func LoadConfig(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	AppConfig = &Config{
		Iot: IotConfig{
			SimulatorEnabled: true,
		},
		LLM: LLMConfig{
			TimeoutSeconds: 30,
			MaxToolRounds:  2,
		},
	}
	if err := yaml.Unmarshal(data, AppConfig); err != nil {
		return err
	}
	applyEnvOverrides()
	return nil
}

func applyEnvOverrides() {
	if AppConfig == nil {
		return
	}
	if value, ok := os.LookupEnv("LLM_ENABLED"); ok {
		if enabled, err := strconv.ParseBool(value); err == nil {
			AppConfig.LLM.Enabled = enabled
		}
	}
	if value := firstEnv("LLM_BASE_URL", "DEEPSEEK_BASE_URL"); value != "" {
		AppConfig.LLM.BaseURL = value
	}
	if value := firstEnv("LLM_API_KEY", "DEEPSEEK_API_KEY"); value != "" {
		AppConfig.LLM.APIKey = value
	}
	if value := firstEnv("LLM_MODEL", "DEEPSEEK_MODEL"); value != "" {
		AppConfig.LLM.Model = value
	}
	if value := firstEnv("LLM_TIMEOUT_SECONDS"); value != "" {
		if seconds, err := strconv.Atoi(value); err == nil {
			AppConfig.LLM.TimeoutSeconds = seconds
		}
	}
	if value := firstEnv("LLM_MAX_TOOL_ROUNDS"); value != "" {
		if rounds, err := strconv.Atoi(value); err == nil {
			AppConfig.LLM.MaxToolRounds = rounds
		}
	}
}

func firstEnv(keys ...string) string {
	for _, key := range keys {
		if value, ok := os.LookupEnv(key); ok {
			return strings.TrimSpace(value)
		}
	}
	return ""
}

func LLMChatCompletionsURL() string {
	if AppConfig == nil {
		return ""
	}
	baseURL := strings.TrimRight(AppConfig.LLM.BaseURL, "/")
	if baseURL == "" {
		return ""
	}
	if strings.HasSuffix(baseURL, "/chat/completions") {
		return baseURL
	}
	if strings.HasSuffix(baseURL, "/v1") {
		return baseURL + "/chat/completions"
	}
	if strings.Contains(baseURL, "api.deepseek.com") {
		return baseURL + "/chat/completions"
	}
	return baseURL + "/v1/chat/completions"
}
