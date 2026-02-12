// SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com>
// SPDX-License-Identifier: Apache-2.0

/*
 * py-jxz Architecture (C4 Model)
 *
 * Python library for building, reading, and verifying .jxz signed containers.
 * This model covers the library itself and its consumers.
 *
 * Version: 0.1.3
 * Format Specification: See jux-container-format/specs/v1/jxz-format.md
 */

workspace "py-jxz" "Python library for building, reading, and verifying .jxz signed containers" {

    model {
        # People
        developer = person "Developer" "Builds or verifies .jxz containers programmatically"
        cliUser = person "CLI User" "Inspects, verifies, or extracts .jxz containers from the command line"

        # External Systems
        pyJuxlib = softwareSystem "py-juxlib" "Client library that enriches JUnit XML reports with metadata" "External System"
        pytestJux = softwareSystem "pytest-jux" "pytest plugin for signing and publishing test reports" "External System"
        behaveJux = softwareSystem "behave-jux" "behave plugin for signing and publishing test reports" "External System"
        spooky = softwareSystem "spooky" "FastAPI server that receives and verifies .jxz containers" "External System"
        juxContainerFormat = softwareSystem "jux-container-format" "Source of truth: .jxz format specification" "Specification"

        # py-jxz System
        pyJxz = softwareSystem "py-jxz" "Python library for .jxz signed container operations" {

            builderContainer = container "Builder" "Assembles .jxz containers from JUnit XML, attachments, and metadata" "Python module (builder.py)" {
                containerBuilder = component "ContainerBuilder" "Public API for building containers: set_report(), add_attachment(), add_meta(), build()" "Python class"
                pathValidator = component "Path Validator" "Rejects path traversal in attachment and metadata names" "Python function"
            }

            readerContainer = container "Reader" "Extracts, validates, and verifies .jxz containers" "Python module (reader.py)" {
                containerReader = component "ContainerReader" "Public API for reading containers: get_report(), validate(), verify()" "Python class"
            }

            manifestContainer = container "Manifest" "Generates and parses JAR-style MANIFEST.MF files" "Python module (manifest.py)" {
                manifestDataclass = component "Manifest" "Dataclass holding main section and per-file entries" "Python dataclass"
                manifestGenerator = component "generate()" "Serializes Manifest to JAR-style text" "Python function"
                manifestParser = component "parse()" "Parses JAR-style text into Manifest with validation" "Python function"
                digestComputer = component "compute_digest()" "Computes SHA-256 hex digest" "Python function"
            }

            signingContainer = container "Signing" "XMLDSIG signing and verification using signxml" "Python module (signing.py)" {
                signFunction = component "sign_manifest()" "Signs manifest text using enveloping XMLDSIG (RSA-SHA256 or ECDSA-SHA256)" "Python function"
                verifyFunction = component "verify_signature()" "Verifies SIGNATURE.XML against manifest text" "Python function"
            }

            errorsContainer = container "Errors" "JxzError exception hierarchy" "Python module (errors.py)" "Supporting"

            cliContainer = container "CLI" "Command-line interface: inspect, verify, extract subcommands" "Python package (cli/)" "CLI" {
                inspectCmd = component "inspect" "Displays container metadata and file inventory (human-readable or JSON)" "Python module (inspect.py)"
                verifyCmd = component "verify" "Verifies container integrity and signatures" "Python module (verify.py)"
                extractCmd = component "extract" "Extracts container contents to disk after digest validation" "Python module (extract.py)"
                cliUtils = component "CLI Utilities" "Shared helpers: format_size(), load_certificate()" "Python module (__init__.py)"
            }
        }

        # Relationships - External consumers to py-jxz
        pyJuxlib -> pyJxz "Uses for container build/read" "Python import"
        pytestJux -> pyJuxlib "Depends on" "Python import"
        behaveJux -> pyJuxlib "Depends on" "Python import"
        spooky -> pyJxz "Uses for container verification" "Python import"
        pyJxz -> juxContainerFormat "Implements" "Specification"

        # Relationships - People
        developer -> pyJxz "Builds and verifies containers" "Python API"
        developer -> builderContainer "Builds containers" "Python API"
        developer -> readerContainer "Reads and verifies containers" "Python API"
        cliUser -> cliContainer "Runs CLI commands" "jxz inspect|verify|extract"

        # Relationships - Container level (for dynamic views)
        builderContainer -> manifestContainer "Computes digests, generates manifest"
        builderContainer -> signingContainer "Signs manifest (optional)"
        readerContainer -> manifestContainer "Parses manifest, validates digests"
        readerContainer -> signingContainer "Verifies signature (if signed)"
        cliContainer -> readerContainer "Opens and processes containers"

        # Relationships - Builder internals
        containerBuilder -> pathValidator "Validates attachment/meta names"
        containerBuilder -> manifestGenerator "Generates MANIFEST.MF"
        containerBuilder -> digestComputer "Computes SHA-256 digests"
        containerBuilder -> signFunction "Signs manifest (optional)"

        # Relationships - Reader internals
        containerReader -> manifestParser "Parses MANIFEST.MF"
        containerReader -> digestComputer "Validates digests"
        containerReader -> verifyFunction "Verifies signature (if signed)"

        # Relationships - CLI to Reader
        inspectCmd -> containerReader "Opens and inspects container"
        inspectCmd -> cliUtils "Formats output"
        verifyCmd -> containerReader "Verifies container"
        verifyCmd -> cliUtils "Loads certificate"
        extractCmd -> containerReader "Reads and validates container"
    }

    views {
        systemContext pyJxz "SystemContext" {
            include *
            autolayout lr
            description "py-jxz in the Jux ecosystem: consumed by client libraries and servers"
        }

        container pyJxz "Containers" {
            include *
            autolayout lr
            description "Internal modules: builder, reader, manifest, signing, errors, CLI"
        }

        component builderContainer "BuilderComponents" {
            include *
            autolayout lr
            description "ContainerBuilder: assembles .jxz from parts with path validation"
        }

        component readerContainer "ReaderComponents" {
            include *
            autolayout lr
            description "ContainerReader: extracts, validates digests, verifies signatures"
        }

        component cliContainer "CLIComponents" {
            include *
            autolayout tb
            description "CLI subcommands: inspect, verify, extract"
        }

        dynamic pyJxz "BuildFlow" "Container build workflow" {
            developer -> builderContainer "1. set_report(), add_attachment(), build()"
            builderContainer -> manifestContainer "2. Compute digests, generate MANIFEST.MF"
            builderContainer -> signingContainer "3. Sign manifest (optional)"
            autolayout lr
        }

        dynamic pyJxz "VerifyFlow" "Container verification workflow" {
            developer -> readerContainer "1. ContainerReader(data)"
            readerContainer -> manifestContainer "2. Parse MANIFEST.MF"
            readerContainer -> signingContainer "3. Verify signature (if signed)"
            readerContainer -> manifestContainer "4. Validate file digests"
            autolayout lr
        }

        styles {
            element "Software System" {
                background #1168bd
                color #ffffff
                shape RoundedBox
            }
            element "External System" {
                background #999999
                color #ffffff
            }
            element "Specification" {
                background #6a1b9a
                color #ffffff
            }
            element "Person" {
                background #08427b
                color #ffffff
                shape Person
            }
            element "Container" {
                background #438dd5
                color #ffffff
                shape RoundedBox
            }
            element "CLI" {
                background #f57c00
                color #ffffff
            }
            element "Supporting" {
                background #85bbf0
                color #000000
            }
            element "Component" {
                background #85bbf0
                color #000000
                shape Component
            }
        }

        theme default
    }

    configuration {
        scope softwaresystem
    }
}
