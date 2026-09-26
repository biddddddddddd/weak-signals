from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawNegativeSignal

MATURE_TECH = [
    # ===== AI / ML (100) =====
    "GPT-4", "GPT-4o", "GPT-4 Turbo", "Claude 3.5 Sonnet", "Claude 3 Opus",
    "Gemini 1.5 Pro", "Gemini 2.0", "Llama 3.1", "Llama 3.2", "Mistral Large",
    "Stable Diffusion", "Stable Diffusion XL", "Midjourney", "DALL-E 3",
    "OpenAI Whisper", "BERT language model", "RoBERTa", "T5", "ELECTRA",
    "Transformer architecture", "Attention mechanism", "Self-attention",
    "RLHF reinforcement learning from human feedback", "DPO",
    "RAG retrieval-augmented generation", "LoRA fine-tuning", "QLoRA",
    "Fine-tuning large language models", "Prompt engineering", "Chain-of-thought prompting",
    "Vector databases Pinecone Weaviate", "FAISS", "Chroma DB", "Qdrant",
    "LangChain framework", "LlamaIndex", "AutoGPT autonomous agents",
    "ChatGPT plugins", "OpenAI API", "Anthropic API", "Hugging Face Transformers",
    "PyTorch", "TensorFlow", "JAX", "ONNX", "scikit-learn", "XGBoost", "LightGBM",
    "CatBoost", "Keras", "FastAI", "MLflow", "Weights & Biases", "DVC",
    "Kubeflow", "Apache Airflow", "Apache Spark MLlib", "Dask", "Ray",
    "Feature stores Feast", "Tecton", "Data versioning DVC",
    "Model monitoring Evidently", "Arize", "WhyLabs",
    "Gradient boosting", "Random forest", "SVM", "k-means clustering",
    "PCA", "t-SNE", "UMAP", "AutoML", "Neural architecture search",
    "Convolutional neural networks", "Recurrent neural networks", "LSTM",
    "GRU", "GANs", "VAEs", "Diffusion models", "Vision transformers",
    "CLIP", "BLIP", "Segment Anything", "YOLO", "ResNet", "EfficientNet",
    "MobileNet", "AlphaGo", "AlphaZero", "MuZero",
    "Deep reinforcement learning", "Q-learning", "PPO", "A3C",
    "Speech recognition", "TTS", "Voice cloning", "Deepfake detection",
    # ===== Инфраструктура / DevOps (80) =====
    "Kubernetes", "Docker", "Podman", "containerd", "Helm", "Istio",
    "Linkerd", "Envoy", "NGINX", "HAProxy", "Traefik",
    "PostgreSQL", "MySQL", "MariaDB", "MongoDB", "Redis", "Cassandra",
    "Elasticsearch", "ClickHouse", "Snowflake", "BigQuery", "Redshift",
    "Apache Kafka", "RabbitMQ", "NATS", "Pulsar",
    "REST API", "GraphQL", "gRPC", "WebSocket", "Server-Sent Events",
    "Microservices", "Service mesh", "API Gateway", "Kong", "Apigee",
    "CI/CD", "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI",
    "Terraform", "Ansible", "Puppet", "Chef", "Pulumi", "CloudFormation",
    "Prometheus", "Grafana", "Datadog", "New Relic", "Dynatrace",
    "ELK Stack", "Loki", "Jaeger", "OpenTelemetry",
    "Git", "GitHub", "GitLab", "Bitbucket", "Mercurial",
    "Linux", "Ubuntu", "Debian", "CentOS", "Red Hat Enterprise Linux",
    "Bash", "PowerShell", "Zsh", "Vim", "Emacs",
    "SSH", "TLS 1.3", "HTTPS", "HTTP/2", "HTTP/3", "IPv6", "DNS",
    "OAuth 2.0", "OpenID Connect", "SAML", "JWT",
    # ===== Облака (40) =====
    "AWS EC2", "AWS S3", "AWS Lambda", "AWS RDS", "AWS DynamoDB",
    "AWS EKS", "AWS Fargate", "AWS CloudFront", "AWS Route 53",
    "Azure Kubernetes Service", "Azure Functions", "Azure Blob Storage",
    "Azure SQL Database", "Azure Cosmos DB", "Azure DevOps",
    "Google Compute Engine", "Google Cloud Storage", "Google BigQuery",
    "Google Kubernetes Engine", "Google Cloud Functions", "Google Cloud Run",
    "Cloudflare Workers", "Cloudflare R2", "Cloudflare D1",
    "DigitalOcean Droplets", "Linode", "Vultr", "Hetzner Cloud",
    "MongoDB Atlas", "Databricks", "Snowflake Data Cloud",
    "Serverless framework", "OpenFaaS", "Knative",
    "Multi-cloud", "Hybrid cloud", "Edge computing CDN",
    "Content delivery networks", "Akamai", "Fastly", "Cloudflare CDN",
    # ===== Стандарты / Регуляции (50) =====
    "ISO 27001", "ISO 9001", "ISO 14001", "ISO 42001",
    "GDPR", "CCPA", "HIPAA", "PCI DSS", "SOC 2", "FedRAMP",
    "NIST Cybersecurity Framework", "NIST AI RMF",
    "EU AI Act", "Digital Services Act", "Digital Markets Act",
    "PSD2", "GDPR", "eIDAS", "MiCA", "DORA",
    "OAuth 2.0", "OpenID Connect", "SAML 2.0", "FIDO2", "WebAuthn",
    "TLS 1.3", "IPsec", "WireGuard", "OpenVPN",
    "HTTP/2", "HTTP/3", "WebSocket", "gRPC", "GraphQL",
    "IPv6", "BGP", "OSPF", "MPLS",
    "REST", "SOAP", "XML", "JSON", "YAML", "TOML",
    "Unicode", "UTF-8", "Base64", "UUID", "ULID",
    # ===== Биотех / Медицина (60) =====
    "CRISPR-Cas9", "CRISPR-Cas12", "Base editing", "Prime editing",
    "mRNA vaccines", "DNA vaccines", "Viral vector vaccines",
    "CAR-T cell therapy", "TCR therapy", "NK cell therapy",
    "Monoclonal antibodies", "Bispecific antibodies", "Antibody-drug conjugates",
    "AlphaFold 2", "AlphaFold 3", "RoseTTAFold", "ESMFold",
    "Nanopore sequencing", "Illumina DNA sequencing", "PacBio sequencing",
    "Liquid biopsy mainstream", "ctDNA analysis", "Single-cell sequencing",
    "Gene therapy general", "AAV vectors", "Lentiviral vectors",
    "Protein structure prediction", "Molecular dynamics simulation",
    "Cryo-EM", "X-ray crystallography", "NMR spectroscopy",
    "PCR", "qPCR", "RT-PCR", "Digital PCR", "NGS",
    "Flow cytometry", "Mass spectrometry", "LC-MS", "MALDI-TOF",
    "Digital therapeutics", "Medical imaging AI", "Radiomics",
    "da Vinci robotic surgery", "Surgical robots", "Capsule endoscopy",
    "FDA-approved AI diagnostics", "CE-marked AI devices",
    "HIPAA cloud compliance", "FHIR healthcare standard", "HL7",
    "EHR and EMR systems", "Epic Systems", "Cerner",
    "Continuous glucose monitors", "Insulin pumps", "Closed-loop systems",
    "Wearable health trackers", "Smartwatch ECG", "Telemedicine",
    # ===== Финтех (60) =====
    "SWIFT", "SEPA", "FedNow", "UPI India", "Pix Brazil",
    "Visa", "Mastercard", "American Express", "UnionPay",
    "Stripe", "PayPal", "Square", "Adyen", "Checkout.com",
    "Open Banking", "PSD2", "PSD3", "Open Finance",
    "ISO 20022", "Nacha", "ACH", "RTGS", "Real-time payments",
    "Blockchain Bitcoin", "Ethereum", "Solana", "Polygon",
    "Stablecoins USDC USDT", "CBDC pilot", "e-CNY",
    "DeFi lending Aave Compound", "Uniswap", "Curve",
    "NFT marketplaces OpenSea", "Blur",
    "Crypto exchanges Binance Coinbase", "Kraken",
    "Custody solutions Fireblocks", "BitGo",
    "KYC AML compliance", "Chainalysis", "Elliptic",
    "RegTech", "SupTech", "WealthTech", "InsurTech",
    "Robo-advisors Betterment", "Wealthfront",
    "Neobanks Revolut", "Monzo", "N26", "Chime",
    "BNPL Klarna Affirm", "Afterpay",
    "Payment orchestration", "Spreedly", "Zooz",
    "Card issuing Marqeta", "Stripe Issuing",
    "Fraud detection Sift", "Forter", "Riskified",
    # ===== Роботы / Автоматизация (40) =====
    "Industrial robots KUKA", "ABB", "Fanuc", "Yaskawa",
    "Collaborative robots Universal Robots", "Cobot",
    "AGV automated guided vehicles", "AMR autonomous mobile robots",
    "Warehouse robots Amazon Robotics", "Locus Robotics", "Fetch",
    "Drone delivery Zipline", "Wing", "Matternet",
    "Autonomous vehicles Waymo", "Cruise", "Tesla FSD",
    "LiDAR Velodyne", "Luminar", "Ouster",
    "SLAM", "ROS Robot Operating System", "ROS 2",
    "Pick-and-place robots", "Bin picking",
    "Welding robots", "Painting robots", "Assembly robots",
    "Surgical robots Intuitive", "Medtronic Hugo",
    "Agricultural robots John Deere", "Harvesting robots",
    "Construction robots", "Demolition robots",
    "Cleaning robots", "Security robots", "Delivery robots",
    "Exoskeletons", "Prosthetics", "Powered exoskeletons",
    "Humanoid robots ASIMO", "Atlas", "Pepper", "NAO",
    # ===== Энергетика / Материалы (50) =====
    "Solar PV", "Perovskite solar cells", "Bifacial solar",
    "Wind turbines", "Offshore wind", "Floating wind",
    "Lithium-ion batteries", "LFP batteries", "NMC batteries",
    "Solid-state batteries", "Sodium-ion batteries",
    "Hydrogen fuel cells", "PEM electrolyzers", "Green hydrogen",
    "Nuclear fission SMR", "Nuclear fusion ITER",
    "Carbon capture DAC", "CCS", "CCUS",
    "Grid-scale storage", "Pumped hydro", "Compressed air storage",
    "Smart grid", "Demand response", "VPP virtual power plants",
    "EV charging networks", "V2G vehicle-to-grid",
    "Heat pumps", "District heating", "Industrial heat",
    "Graphene", "Carbon nanotubes", "MXenes",
    "Quantum dots", "2D materials MoS2", "Perovskites",
    "Metamaterials", "Aerogels", "Metal-organic frameworks",
    "Additive manufacturing 3D printing", "SLM", "FDM", "SLA",
    "CNC machining", "Injection molding", "Composites",
    "Recycling technologies", "Circular economy",
    "Desalination", "Water treatment", "Atmospheric water harvesting",
]


def collect():
    db = SessionLocal()
    saved = 0
    try:
        for name in MATURE_TECH:
            if db.query(RawNegativeSignal).filter(RawNegativeSignal.name == name).first():
                continue
            db.add(RawNegativeSignal(
                name=name,
                description="Зрелая технология, массовое внедрение, устоявшийся рынок",
                source="mature_list",
                year=2020,
            ))
            saved += 1
        db.commit()
        logger.info(f"[negative] saved {saved}, total in list: {len(MATURE_TECH)}")
    except Exception as e:
        db.rollback()
        logger.error(f"[negative] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    collect()