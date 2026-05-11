package iot

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

type MqttAdapter struct {
	client    mqtt.Client
	broker    string
	clientId  string
	handlers  map[string]MessageHandler
	mu        sync.RWMutex
	connected bool
}

type MessageHandler func(deviceId string, data SensorData)

func NewMqttAdapter(broker, clientId string) *MqttAdapter {
	return &MqttAdapter{
		broker:   broker,
		clientId: clientId,
		handlers: make(map[string]MessageHandler),
	}
}

func (a *MqttAdapter) Connect() error {
	opts := mqtt.NewClientOptions()
	opts.AddBroker(a.broker)
	opts.SetClientID(a.clientId)
	opts.SetAutoReconnect(true)
	opts.SetMaxReconnectInterval(10 * time.Second)
	opts.SetConnectRetry(true)
	opts.SetConnectRetryInterval(5 * time.Second)

	opts.SetOnConnectHandler(func(c mqtt.Client) {
		a.mu.Lock()
		a.connected = true
		a.mu.Unlock()
		fmt.Println("MQTT connected to", a.broker)
		a.resubscribeAll()
	})

	opts.SetConnectionLostHandler(func(c mqtt.Client, err error) {
		a.mu.Lock()
		a.connected = false
		a.mu.Unlock()
		fmt.Println("MQTT connection lost:", err)
	})

	a.client = mqtt.NewClient(opts)
	token := a.client.Connect()
	if token.Wait() && token.Error() != nil {
		return token.Error()
	}
	return nil
}

func (a *MqttAdapter) IsConnected() bool {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.connected
}

func (a *MqttAdapter) Subscribe(deviceId, topic string, handler MessageHandler) error {
	a.mu.Lock()
	a.handlers[topic] = handler
	a.mu.Unlock()

	if a.client == nil || !a.client.IsConnected() {
		return nil
	}

	token := a.client.Subscribe(topic, 0, func(c mqtt.Client, msg mqtt.Message) {
		var data SensorData
		if err := json.Unmarshal(msg.Payload(), &data); err != nil {
			fmt.Printf("MQTT parse error for topic %s: %v\n", topic, err)
			return
		}
		data.DeviceId = deviceId
		data.Timestamp = time.Now().UnixMilli()
		a.mu.RLock()
		h, ok := a.handlers[topic]
		a.mu.RUnlock()
		if ok {
			h(deviceId, data)
		}
	})
	token.Wait()
	return token.Error()
}

func (a *MqttAdapter) Unsubscribe(topic string) {
	a.mu.Lock()
	delete(a.handlers, topic)
	a.mu.Unlock()
	if a.client != nil && a.client.IsConnected() {
		a.client.Unsubscribe(topic)
	}
}

func (a *MqttAdapter) Disconnect() {
	if a.client != nil && a.client.IsConnected() {
		a.client.Disconnect(250)
	}
}

func (a *MqttAdapter) resubscribeAll() {
	a.mu.RLock()
	topics := make([]string, 0, len(a.handlers))
	for t := range a.handlers {
		topics = append(topics, t)
	}
	a.mu.RUnlock()

	for _, topic := range topics {
		a.mu.RLock()
		_, ok := a.handlers[topic]
		a.mu.RUnlock()
		if ok {
			a.client.Subscribe(topic, 0, func(c mqtt.Client, msg mqtt.Message) {
				a.mu.RLock()
				h, ok := a.handlers[msg.Topic()]
				a.mu.RUnlock()
				if ok {
					var data SensorData
					if err := json.Unmarshal(msg.Payload(), &data); err != nil {
						return
					}
					data.Timestamp = time.Now().UnixMilli()
					h(data.DeviceId, data)
				}
			})
		}
	}
}
