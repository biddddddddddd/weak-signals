from loguru import logger
from src.db.connection import SessionLocal
from src.db.models import RawNegativeSignal

# 600 зрелых технологий (которых ещё нет в базе)
MATURE_TECH = [
    # ===== AI / ML (новые, 100) =====
    "GPT-3.5", "GPT-3", "Claude 2", "Claude Instant", "Gemini 1.0",
    "PaLM 2", "Bard", "LLaMA 2", "Mistral 7B", "Mixtral 8x7B",
    "Falcon LLM", "Vicuna", "Alpaca", "Guanaco", "WizardLM",
    "Phi-2", "Phi-3", "Qwen 1.5", "Yi-34B", "DeepSeek LLM",
    "StableLM", "RedPajama", "MPT-7B", "Dolly", "Koala",
    "OpenAssistant", "BLOOM", "OPT-175B", "Galactica", "GPT-NeoX",
    "Codex", "GitHub Copilot", "CodeWhisperer", "Tabnine", "Replit Ghostwriter",
    "Cursor IDE", "Codeium", "Sourcegraph Cody", "Continue.dev", "Aider",
    "Stable Diffusion 2.1", "SDXL Turbo", "Playground AI", "Leonardo AI", "Ideogram",
    "Runway Gen-2", "Pika Labs", "Stable Video Diffusion", "Sora", "Veo",
    "ElevenLabs", "Play.ht", "Resemble AI", "Descript", "Murf AI",
    "Suno AI", "Udio", "Stable Audio", "MusicGen", "AudioCraft",
    "Segment Anything 2", "DINOv2", "CLIP 2", "BLIP-2", "LLaVA",
    "Flamingo", "Kosmos-1", "GPT-4V", "Gemini Vision", "Claude Vision",
    "Whisper Large v3", "Deepgram", "AssemblyAI", "Rev AI", "Otter.ai",
    "Replicate", "Together AI", "Anyscale", "Modal", "Banana Dev",
    "Pinecone", "Weaviate", "Qdrant", "Milvus", "Chroma",
    "LangChain", "LlamaIndex", "Haystack", "Semantic Kernel", "AutoGen",
    "CrewAI", "AutoGPT", "BabyAGI", "AgentGPT", "SuperAGI",
    "Flowise", "LangFlow", "Dify", "Rivet", "Voiceflow",
    # ===== Инфраструктура (новые, 80) =====
    "Nomad", "Consul", "Vault", "Packer", "Vagrant",
    "Rancher", "OpenShift", "Tanzu", "Anthos", "EKS Anywhere",
    "K3s", "K0s", "MicroK8s", "Minikube", "Kind",
    "Cilium", "Calico", "Flannel", "Weave Net", "Multus",
    "ArgoCD", "FluxCD", "Spinnaker", "Tekton", "Drone CI",
    "Jenkins X", "Buildkite", "TeamCity", "Bamboo", "Concourse",
    "Prometheus Operator", "Thanos", "Cortex", "VictoriaMetrics", "Mimir",
    "Fluentd", "Fluent Bit", "Vector", "Logstash", "Filebeat",
    "Jaeger", "Zipkin", "Tempo", "SkyWalking", "Pinpoint",
    "OpenTelemetry Collector", "Datadog Agent", "New Relic Agent", "Dynatrace OneAgent", "AppDynamics",
    "Redis Cluster", "Redis Sentinel", "KeyDB", "Dragonfly", "Memcached",
    "MongoDB Atlas", "DocumentDB", "Couchbase", "CouchDB", "RethinkDB",
    "Neo4j", "ArangoDB", "JanusGraph", "TigerGraph", "Amazon Neptune",
    "InfluxDB", "TimescaleDB", "QuestDB", "VictoriaMetrics", "TDengine",
    "ClickHouse Cloud", "Snowflake", "Databricks", "BigQuery", "Redshift",
    "dbt", "Airbyte", "Fivetran", "Stitch", "Meltano",
    "Apache Flink", "Apache Beam", "Apache Storm", "Apache Samza", "Kafka Streams",
    "Apache NiFi", "Apache Airflow", "Prefect", "Dagster", "Luigi",
    # ===== Облака (новые, 60) =====
    "AWS ECS", "AWS ECR", "AWS EFS", "AWS FSx", "AWS Batch",
    "AWS Step Functions", "AWS EventBridge", "AWS SQS", "AWS SNS", "AWS Kinesis",
    "AWS Glue", "AWS Athena", "AWS EMR", "AWS SageMaker", "AWS Bedrock",
    "Azure Container Apps", "Azure Container Instances", "Azure App Service", "Azure Functions", "Azure Logic Apps",
    "Azure Service Bus", "Azure Event Grid", "Azure Event Hubs", "Azure Data Factory", "Azure Synapse",
    "Azure Machine Learning", "Azure OpenAI", "Azure Cognitive Services", "Azure Bot Service", "Azure Maps",
    "GCP Cloud Run", "GCP Cloud Functions", "GCP App Engine", "GCP GKE Autopilot", "GCP Cloud Build",
    "GCP Pub/Sub", "GCP Dataflow", "GCP Dataproc", "GCP Vertex AI", "GCP Gemini API",
    "GCP Cloud Spanner", "GCP Firestore", "GCP Bigtable", "GCP Memorystore", "GCP Filestore",
    "Oracle Cloud Infrastructure", "OCI Compute", "OCI Object Storage", "OCI Autonomous Database", "OCI Functions",
    "IBM Cloud", "IBM Watson", "IBM Cloud Kubernetes", "IBM Db2", "IBM MQ",
    "Alibaba Cloud", "Alibaba ECS", "Alibaba OSS", "Alibaba MaxCompute", "Alibaba PAI",
    "Yandex Cloud", "Yandex Compute", "Yandex Object Storage", "Yandex Managed Kubernetes", "Yandex DataSphere",
    # ===== Стандарты / Регуляции (новые, 50) =====
    "ISO 22301", "ISO 31000", "ISO 45001", "ISO 50001", "ISO 20000",
    "IEC 62443", "NIST 800-53", "NIST 800-171", "NIST CSF 2.0", "CIS Controls",
    "PCI DSS 4.0", "SOC 1", "SOC 3", "HITRUST", "ISO 27701",
    "CCPA 2.0", "CPRA", "LGPD", "PIPL", "POPIA",
    "ePrivacy Directive", "NIS2 Directive", "Cyber Resilience Act", "Data Act", "AI Act",
    "FIPS 140-3", "Common Criteria", "FIDO2", "WebAuthn", "CTAP2",
    "OpenID Connect 1.0", "OAuth 2.1", "SAML 2.0", "WS-Federation", "Kerberos",
    "LDAP v3", "RADIUS", "TACACS+", "Diameter", "SIP",
    "RTP", "RTCP", "RTSP", "HLS", "DASH",
    "WebRTC", "WebTransport", "QUIC", "HTTP/3", "MQTT",
    # ===== Биотех / Медицина (новые, 60) =====
    "CRISPR-Cas13", "CRISPR interference", "CRISPR activation", "CasMINI", "Cas12a",
    "Prime editing PE2", "Prime editing PE3", "Base editor BE3", "Base editor ABE", "Cytosine base editor",
    "Adenine base editor", "PAM-free Cas9", "HiFi Cas9", "eSpCas9", "SpCas9-NG",
    "Long-read sequencing", "Oxford Nanopore MinION", "PacBio Sequel II", "PacBio Revio", "Illumina NovaSeq",
    "Illumina MiSeq", "Illumina NextSeq", "BGI DNBSEQ", "MGI T7", "Roche 454",
    "Sanger sequencing", "Massively parallel sequencing", "Single-cell RNA-seq", "Spatial transcriptomics", "10x Genomics",
    "Visium", "Xenium", "MERFISH", "seqFISH", "Slide-seq",
    "CITE-seq", "REAP-seq", "Multiome", "ATAC-seq", "ChIP-seq",
    "Hi-C", "Micro-C", "Omni-C", "Hi-C 2.0", "Hi-C 3.0",
    "AlphaMissense", "ESM-2", "ESM-3", "RoseTTAFold2", "OpenFold",
    "RFdiffusion", "ProteinMPNN", "AlphaFold-Multimer", "ColabFold", "OmegaFold",
    "CAR-T Yescarta", "CAR-T Kymriah", "CAR-T Breyanzi", "CAR-T Abecma", "CAR-T Carvykti",
    "TCR T-cell therapy", "TIL therapy", "NK cell therapy", "Gamma delta T cells", "iPSC-derived NK",
    # ===== Финтех (новые, 60) =====
    "FedNow", "RTP Network", "TCH", "Nacha ACH", "Same Day ACH",
    "SWIFT gpi", "SWIFT MT", "SWIFT MX", "SWIFT ISO 20022", "CBPR+",
    "SEPA Instant", "SEPA Credit Transfer", "SEPA Direct Debit", "TARGET2", "T2S",
    "PIX Brazil", "UPI India", "PayNow Singapore", "PromptPay Thailand", "DuitNow Malaysia",
    "Faster Payments UK", "NPP Australia", "NIP Nigeria", "M-Pesa", "Airtel Money",
    "Visa Direct", "Mastercard Send", "RTP Visa", "Cross-Border Visa B2B", "Mastercard Cross-Border",
    "Stripe Connect", "Stripe Treasury", "Stripe Issuing", "Stripe Terminal", "Stripe Tax",
    "PayPal Braintree", "PayPal Venmo", "PayPal Honey", "PayPal Zettle", "PayPal Xoom",
    "Square Cash App", "Square Reader", "Square Terminal", "Square Online", "Square Banking",
    "Adyen for Platforms", "Adyen Risk", "Adyen Unified Commerce", "Adyen Terminal", "Adyen Payouts",
    "Open Banking UK", "PSD2 XS2A", "Berlin Group", "STET", "Open Finance Brazil",
    "ISO 8583", "ISO 20022", "NACHA", "Bacs", "CHAPS",
    # ===== Роботы / Автоматизация (новые, 50) =====
    "UR5", "UR10", "UR16", "UR20", "UR30",
    "ABB YuMi", "ABB GoFa", "ABB SWIFTI", "ABB IRB 1100", "ABB IRB 4600",
    "Fanuc CRX", "Fanuc LR Mate", "Fanuc M-10", "Fanuc R-2000", "Fanuc SCARA",
    "KUKA LBR iiwa", "KUKA KR AGILUS", "KUKA KR CYBERTECH", "KUKA KR IONTEC", "KUKA LBR Med",
    "Yaskawa HC10", "Yaskawa GP7", "Yaskawa MH5", "Yaskawa SDA10F", "Yaskawa PL80",
    "Boston Dynamics Spot", "Boston Dynamics Atlas", "Boston Dynamics Stretch", "Handle", "BigDog",
    "Agility Digit", "Agility Cassie", "ANYbotics ANYmal", "Ghost Robotics Vision 60", "Unitree Go2",
    "Unitree B2", "Unitree H1", "Unitree G1", "Xiaomi CyberDog", "Xiaomi CyberOne",
    "Tesla Optimus", "Figure 01", "Figure 02", "1X Neo", "1X Eve",
    "Apptronik Apollo", "Sanctuary Phoenix", "Phoenix 6", "PAL TIAGo", "PAL REEM",
    # ===== Энергетика / Материалы (новые, 50) =====
    "Monocrystalline silicon", "Polycrystalline silicon", "Thin-film CdTe", "CIGS solar", "Amorphous silicon",
    "Perovskite-silicon tandem", "All-perovskite tandem", "Organic photovoltaics", "Quantum dot solar", "Dye-sensitized solar",
    "Onshore wind", "Offshore fixed wind", "Offshore floating wind", "Vertical axis wind", "Airborne wind",
    "LFP battery", "NMC 811", "NMC 622", "NCA battery", "LTO battery",
    "Sodium-ion battery", "Potassium-ion battery", "Magnesium-ion battery", "Aluminum-air battery", "Zinc-air battery",
    "Solid-state sulfide", "Solid-state oxide", "Solid-state polymer", "Lithium-metal anode", "Silicon anode",
    "PEM fuel cell", "SOFC fuel cell", "AFC fuel cell", "PAFC fuel cell", "MCFC fuel cell",
    "Alkaline electrolyzer", "PEM electrolyzer", "SOEC electrolyzer", "AEM electrolyzer", "Anion exchange membrane",
    "Small modular reactor", "Microreactor", "Molten salt reactor", "Fast breeder reactor", "Fusion tokamak",
    # ===== Материалы / Производство (новые, 40) =====
    "Carbon fiber composites", "Glass fiber composites", "Aramid fiber Kevlar", "UHMWPE", "PEEK",
    "Graphene oxide", "Reduced graphene oxide", "Carbon nanotube", "Fullerene", "Diamond-like carbon",
    "Metal-organic frameworks", "Covalent organic frameworks", "Zeolites", "Activated carbon", "Silica aerogel",
    "Perovskite solar", "Quantum dots CdSe", "Quantum dots InP", "Quantum dots perovskite", "2D MoS2",
    "2D WS2", "2D hBN", "2D black phosphorus", "2D MXenes", "2D antimonene",
    "Additive FDM", "Additive SLA", "Additive SLS", "Additive SLM", "Additive DMLS",
    "Additive EBM", "Additive DED", "Additive Binder Jetting", "Additive Material Jetting", "Additive PolyJet",
    "CNC 5-axis", "CNC Swiss-type", "CNC EDM", "CNC Wire EDM", "CNC Waterjet",
]


def add():
    db = SessionLocal()
    saved = 0
    skipped = 0
    try:
        for name in MATURE_TECH:
            if db.query(RawNegativeSignal).filter(RawNegativeSignal.name == name).first():
                skipped += 1
                continue
            db.add(RawNegativeSignal(
                name=name,
                description="Зрелая технология, массовое внедрение, устоявшийся рынок",
                source="mature_batch_2",
                year=2020,
            ))
            saved += 1
        db.commit()
        logger.info(f"[negative batch] saved {saved}, skipped {skipped}, total in list {len(MATURE_TECH)}")
    except Exception as e:
        db.rollback()
        logger.error(f"[negative batch] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    add()