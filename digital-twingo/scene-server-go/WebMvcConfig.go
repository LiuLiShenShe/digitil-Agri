package main

// WebMvcConfig is handled in SceneServerApplication.go via gin-contrib/cors middleware.
// The CORS policy mirrors the Java WebMvcConfig:
//   - AllowCredentials: true
//   - AllowedOriginPatterns: "*"
//   - AllowedMethods: GET, POST, DELETE, PUT
//   - AllowedHeaders: "*"
//   - MaxAge: 1800 seconds
//
// See SceneServerApplication.go for the cors.New() configuration.
