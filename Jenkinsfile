pipeline {
    agent worker-1
 
    environment {
        // ── Google Cloud ──────────────────────────────────────────────
        // Auth via VM's attached service account — no credential needed.
        GCS_BUCKET          = credentials('gcs-bucket-name')
        GCS_OBJECT_PATH     = credentials('gcs-object-path')
 
        // ── Groq (LLM — graph extraction) ────────────────────────────
        // Free tier: https://console.groq.com -> API Keys
        GROQ_API_KEY        = credentials('groq-api-key')
        GROQ_BASE_URL       = 'https://api.groq.com/openai/v1'
        LLM_MODEL           = 'llama-3.3-70b-versatile'
 
        // ── LiteLLM / Qwen2.5 (Embeddings) ───────────────────────────
        // Qwen embedding model served via LiteLLM on GKE.
        // No auth on the gateway — dummy key satisfies the OpenAI client's
        // requirement for a non-empty Authorization header.
        LITELLM_BASE_URL    = 'http://34.139.139.250/v1'
        LITELLM_API_KEY     = 'no-auth'
        EMBEDDING_MODEL     = 'qwen-embedding'
        EMBEDDING_DIMENSION = '1536'
 
        // ── Neo4j ─────────────────────────────────────────────────────
        // No auth configured — connecting without username/password.
        NEO4J_URI           = credentials('neo4j-uri')
 
        // ── Qdrant ────────────────────────────────────────────────────
        // No auth configured — connecting without API key.
        QDRANT_HOST         = credentials('qdrant-host')
        QDRANT_COLLECTION   = 'document_embeddings'
 
        // ── Pipeline config ───────────────────────────────────────────
        CHUNK_SIZE          = '512'
        CHUNK_OVERLAP       = '64'
        PYTHON_VENV         = "${WORKSPACE}/.venv"
        ARTIFACTS_DIR       = "${WORKSPACE}/artifacts"
    }
 
    options {
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }
 
    stages {
 
        stage('Setup') {
            steps {
                sh 'bash scripts/setup.sh'
            }
        }
 
        stage('Pull from GCS') {
            steps {
                sh '. ${PYTHON_VENV}/bin/activate && python3 scripts/pull_gcs.py'
                script {
                    env.DOWNLOADED_FILE = sh(
                        script: "cat '${ARTIFACTS_DIR}/.downloaded_file'",
                        returnStdout: true
                    ).trim()
                }
            }
        }
 
        stage('Parse & Chunk') {
            steps {
                sh '. ${PYTHON_VENV}/bin/activate && python3 scripts/parse_and_chunk.py'
            }
        }
 
        stage('Generate Embeddings') {
            steps {
                sh '. ${PYTHON_VENV}/bin/activate && python3 scripts/generate_embeddings.py'
            }
        }
 
        stage('Build Knowledge Graph') {
            steps {
                sh '. ${PYTHON_VENV}/bin/activate && python3 scripts/build_graph.py'
            }
        }
 
        stage('Store → Neo4j & Qdrant') {
            parallel {
                stage('Neo4j') {
                    steps {
                        sh '. ${PYTHON_VENV}/bin/activate && python3 scripts/store_neo4j.py'
                    }
                }
                stage('Qdrant') {
                    steps {
                        sh '. ${PYTHON_VENV}/bin/activate && python3 scripts/store_qdrant.py'
                    }
                }
            }
        }
 
        stage('Verify') {
            steps {
                sh '. ${PYTHON_VENV}/bin/activate && python3 scripts/verify.py'
            }
        }
    }
 
    post {
        always {
            node(null) {
                archiveArtifacts(
                    artifacts: 'artifacts/pipeline_report.json, artifacts/chunks.json, artifacts/knowledge_graph.json',
                    allowEmptyArchive: true
                )
                // Guard against DOWNLOADED_FILE being empty if pipeline failed early
                sh '''
                    if [ -n "${DOWNLOADED_FILE:-}" ]; then
                        rm -f "${ARTIFACTS_DIR}/${DOWNLOADED_FILE}" || true
                    fi
                    rm -f "${ARTIFACTS_DIR}/chunks_with_embeddings.json" || true
                '''
            }
        }
        success { echo ' Pipeline completed successfully!' }
        failure { echo ' Pipeline failed — check stage logs above.' }
    }
}
