package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Server   ServerConfig   `yaml:"server"`
	Spring   SpringConfig   `yaml:"spring"`
	Mybatis  MybatisConfig  `yaml:"mybatis"`
	Swagger  SwaggerConf    `yaml:"swagger"`
	Iot      IotConfig      `yaml:"iot"`
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
	MqttBroker   string `yaml:"mqtt-broker"`
	MqttClientId string `yaml:"mqtt-client-id"`
	SimulatorEnabled bool `yaml:"simulator-enabled"`
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
	}
	return yaml.Unmarshal(data, AppConfig)
}
