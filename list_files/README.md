# Bio-Formats Gradle Project

A simple Gradle project demonstrating the use of [Bio-Formats](https://github.com/ome/bioformats) v8.3.0 for reading and processing life sciences image file formats.

## Overview

Bio-Formats is a Java library for reading and writing data in life sciences image file formats. This project provides a minimal working example of how to integrate Bio-Formats into a Gradle-based Java application.

## Features

- **Latest Bio-Formats**: Uses Bio-Formats v8.3.0
- **Simple Structure**: No package hierarchy, single main class
- **Comprehensive Example**: Demonstrates reading image metadata and properties
- **Format Support**: Shows all supported file formats
- **Gradle Build**: Clean Gradle build configuration with minimal dependencies

## Prerequisites

- Java 11 or higher
- Gradle 7.0 or higher (or use the Gradle wrapper)

## Getting Started

### 1. Build the Project

```bash
./gradlew build
```

### 2. Run the Application

To see supported formats:
```bash
./gradlew run
```

To analyze a specific image file:
```bash
./gradlew run --args="path/to/your/image.tif"
```

## Supported Formats

Bio-Formats supports over 150 file formats including:

- **Microscopy formats**: LSM, CZI, ND2, LIF, OIB, VSI
- **Standard formats**: TIFF, JPEG, PNG, BMP
- **Medical imaging**: DICOM
- **And many more...**

## Project Structure

```
├── build.gradle              # Gradle build configuration
├── gradle.properties         # Gradle properties
├── settings.gradle           # Gradle settings
├── src/
│   └── main/java/
│       └── ShowFiles.java    # Main application class
└── README.md
```

## Dependencies

- **Bio-Formats**: `ome:bioformats_package:8.3.0` (complete package with all readers)
- **Logging**: `ch.qos.logback:logback-classic:1.4.14`

## Usage Examples

### Reading Image Metadata

```java
ShowFiles app = new ShowFiles();
app.readImageInfo("sample.tif");
```

### Displaying Supported Formats

```java
ShowFiles.displaySupportedFormats();
```

## Configuration

The project is configured with:

- **Java 11** compatibility
- **OME Artifactory** repository for Bio-Formats dependencies
- **Unidata repository** for NetCDF dependencies
- **Optimized JVM settings** in `gradle.properties`

## License

This example project is provided as-is for demonstration purposes. Bio-Formats itself is licensed under the GNU General Public License (GPL); commercial licenses are available from Glencoe Software.

## Resources

- [Bio-Formats Documentation](https://bio-formats.readthedocs.io/)
- [Bio-Formats GitHub Repository](https://github.com/ome/bioformats)
- [Bio-Formats Examples](https://github.com/ome/bio-formats-examples)
- [Open Microscopy Environment](https://www.openmicroscopy.org/)
