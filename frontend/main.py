import re
import streamlit as st
import yaml
import os


config_template = {
    "automation": {
        "project": "",
        "bucket": {},
        "service_accounts": {}
    },
    "billing_account": "",
    "name": "",
    "parent": "",
    "prefix": "",
    "billing_budgets": [],
    "buckets": {},
    "iam": {},
    "iam_by_principals": {},
    "labels": {},
    "contacts": {},
    "metric_scopes": [],
    "org_policies": {},
    "service_accounts": {},
    "service_encryption_key_ids": {},
    "services": [],
    "shared_vpc_host_config": {},
    "shared_vpc_service_project_config": {},
    "tag_bindings": {},
    "vpc_sc": {},
}

def save_yaml(data, filename="config.yaml"):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, "w") as file:
        yaml.dump(data, file, default_flow_style=False)
    st.success(f"A konfiguráció mentve: {filepath}")
    
    yaml_str = yaml.dump(data, default_flow_style=False)
    st.download_button(
        label="Download Configuration",
        data=yaml_str,
        file_name=filename,
        mime="text/yaml"
    )

def render_iam_config(iam_key, iam_data):
    st.write(f"IAM Configuration for {iam_key}")

    if iam_key not in st.session_state:
        st.session_state[iam_key] = iam_data

    new_role = st.text_input(
        "Add new role (must start with 'roles/'):",
        key=f"new_role_input_{iam_key}", 
    )

    if st.button("Add Role", key=f"add_role_button_{iam_key}"):
        if new_role:
            if not new_role.startswith("roles/"):
                st.error("Role must start with 'roles/'!")
            else:
                if new_role not in st.session_state[iam_key]:
                    st.session_state[iam_key][new_role] = []
                    st.success(f"Added new role: {new_role}")
                else:
                    st.error("Role already exists!")
        else:
            st.error("Role name cannot be empty!")

    for role, values in st.session_state[iam_key].items():
        st.write(f"Role: {role}")
        new_values = st.text_area(
            f"Edit values for {role} (comma-separated):",
            value=", ".join(values),
            key=f"edit_{role}_{iam_key}",
            height=100,
        )
        pattern = re.compile(r"^(?:domain:|group:|serviceAccount:|user:|principal:|principalSet:|[a-z])")
        values = [v.strip() for v in new_values.split(",") if v.strip()]
        if all(pattern.match(v) for v in values):
            st.session_state[iam_key][role] = values
        else:
            st.error("Invalid value format! Must be domain, group, serviceAccount, user, principal, principalSet, or lowercase letter.")

    for role in list(st.session_state[iam_key].keys()):
        if st.button(f"Delete {role}", key=f"delete_{role}_{iam_key}"):
            del st.session_state[iam_key][role]
            st.rerun()

    return st.session_state[iam_key]

def get_existing_roles(iam_data):
    return list(iam_data.keys())

def validate_condition(condition):
    if not condition.get("expression"):
        return False, "Expression is required!"
    if not condition.get("title"):
        return False, "Title is required!"
    return True, None

def render_iam_bindings(existing_roles, key_prefix):
    tab1, tab2 = st.tabs(["Standard IAM Bindings", "Additive IAM Bindings"])
    
    with tab1:
        iam_bindings = _render_standard_iam_bindings(existing_roles, key_prefix)
    
    with tab2:
        iam_additive_bindings = _render_additive_iam_bindings(existing_roles, key_prefix)

    return {
        "standard": iam_bindings,
        "additive": iam_additive_bindings
    }

def _render_standard_iam_bindings(existing_roles, key_prefix = ""):
    st.subheader("Standard IAM Bindings (members array)")

    session_key = f"{key_prefix}_iam_bindings"
    
    if session_key not in st.session_state:
        st.session_state[session_key] = {}

    with st.container(border=True):
        cols = st.columns([2, 3])
        with cols[0]:
            new_binding_key = st.text_input(
                "New binding key:",
                help="a-z, 0-9, _, - only",
                key=f"new_std_binding_{key_prefix}"
            )
        with cols[1]:
            selected_role = st.selectbox(
                "Select role:",
                options=existing_roles,
                key=f"select_std_role_{key_prefix}",
                index=0
            )
        
        if st.button("Add Standard Binding", key=f"add_std_binding_{key_prefix}"):
            if not new_binding_key:
                st.error("Binding key is required!")
            elif not re.match(r"^[a-z0-9_-]+$", new_binding_key):
                st.error("Use only lowercase letters, numbers, underscores and hyphens")
            elif new_binding_key in st.session_state[session_key]:
                st.error("Key already exists!")
            else:
                st.session_state[session_key][new_binding_key] = {
                    "members": [],
                    "role": selected_role,
                    "condition": {
                        "expression": "",
                        "title": "",
                        "description": ""
                    }
                }
                st.rerun()
    
    for binding_key in list(st.session_state[session_key].keys()):
        binding = st.session_state[session_key][binding_key]
        
        with st.expander(f"Binding: {binding_key}", expanded=True):
            cols = st.columns([4, 1])
            with cols[1]:
                if st.button("🗑️", key=f"del_std_{binding_key}_{key_prefix}"):
                    del st.session_state[session_key][binding_key]
                    st.rerun()
                    return
            
            current_role_index = existing_roles.index(binding["role"]) if binding["role"] in existing_roles else 0
            binding["role"] = st.selectbox(
                "Role:",
                options=existing_roles,
                index=current_role_index,
                key=f"std_role_{binding_key}_{key_prefix}"
            )
            
            members = st.text_area(
                "Members (comma separated):",
                value=", ".join(binding["members"]),
                key=f"std_members_{binding_key}_{key_prefix}",
                help="Format: domain:|group:|serviceAccount:|user:|principal:|principalSet:|[a-z]"
            )
            validated_members = []
            for m in [x.strip() for x in members.split(",") if x.strip()]:
                if re.match(r"^(?:domain:|group:|serviceAccount:|user:|principal:|principalSet:|[a-z])", m):
                    validated_members.append(m)
                else:
                    st.error(f"Invalid member: {m}")
            binding["members"] = validated_members
            
            st.write("Condition:")
            binding["condition"]["expression"] = st.text_input(
                "Expression*",
                value=binding["condition"]["expression"],
                key=f"std_expr_{binding_key}_{key_prefix}"
            )
            binding["condition"]["title"] = st.text_input(
                "Title*",
                value=binding["condition"]["title"],
                key=f"std_title_{binding_key}_{key_prefix}"
            )
            binding["condition"]["description"] = st.text_input(
                "Description",
                value=binding["condition"]["description"],
                key=f"std_desc_{binding_key}_{key_prefix}"
            )

    return st.session_state[session_key]

def _render_additive_iam_bindings(existing_roles, key_prefix = ""):
    st.subheader("Additive IAM Bindings (single member)")

    session_key = f"{key_prefix}_iam_bindings_additive"
    
    if session_key not in st.session_state:
        st.session_state[session_key] = {}
    
    with st.container(border=True):
        cols = st.columns([2, 3])
        with cols[0]:
            new_binding_key = st.text_input(
                "New binding key:",
                help="a-z, 0-9, _, - only",
                key=f"new_add_binding_{key_prefix}"
            )
        with cols[1]:
            selected_role = st.selectbox(
                "Select role:",
                options=existing_roles,
                key=f"select_add_role_{key_prefix}",
                index=0
            )
        
        if st.button("Add Additive Binding", key=f"add_add_binding_{key_prefix}"):
            if not new_binding_key:
                st.error("Binding key is required!")
            elif not re.match(r"^[a-z0-9_-]+$", new_binding_key):
                st.error("Use only lowercase letters, numbers, underscores and hyphens")
            elif new_binding_key in st.session_state[session_key]:
                st.error("Key already exists!")
            else:
                st.session_state[session_key][new_binding_key] = {
                    "member": "",
                    "role": selected_role,
                    "condition": {
                        "expression": "",
                        "title": "",
                        "description": ""
                    }
                }
                st.rerun()
    
    for binding_key in list(st.session_state[session_key].keys()):
        binding = st.session_state[session_key][binding_key]
        
        with st.expander(f"Binding: {binding_key}", expanded=True):
            cols = st.columns([4, 1])
            with cols[1]:
                if st.button("🗑️", key=f"del_add_{binding_key}_{key_prefix}"):
                    del st.session_state[session_key][binding_key]
                    st.rerun()
                    return
            
            current_role_index = existing_roles.index(binding["role"]) if binding["role"] in existing_roles else 0
            binding["role"] = st.selectbox(
                "Role:",
                options=existing_roles,
                index=current_role_index,
                key=f"add_role_{binding_key}_{key_prefix}"
            )
            
            binding["member"] = st.text_input(
                "Member:",
                value=binding["member"],
                key=f"add_member_{binding_key}_{key_prefix}",
                help="Format: domain:|group:|serviceAccount:|user:|principal:|principalSet:|[a-z]"
            )
            if binding["member"] and not re.match(r"^(?:domain:|group:|serviceAccount:|user:|principal:|principalSet:|[a-z])", binding["member"]):
                st.error("Invalid member format!")
            
            st.write("Condition:")
            binding["condition"]["expression"] = st.text_input(
                "Expression*",
                value=binding["condition"]["expression"],
                key=f"add_expr_{binding_key}_{key_prefix}"
            )
            binding["condition"]["title"] = st.text_input(
                "Title*",
                value=binding["condition"]["title"],
                key=f"add_title_{binding_key}_{key_prefix}"
            )
            binding["condition"]["description"] = st.text_input(
                "Description",
                value=binding["condition"]["description"],
                key=f"add_desc_{binding_key}_{key_prefix}"
            )

    return st.session_state[session_key]

def can_save_config(iam_bindings_data):
    for binding_data in iam_bindings_data.values():
        is_valid, _ = validate_condition(binding_data["condition"])
        if not is_valid:
            return False
    return True

def render_labels(labels_dict, key_prefix):
    session_key = f"{key_prefix}_labels"
    if session_key not in st.session_state:
        st.session_state[session_key] = labels_dict.copy()
    
    st.write("Labels")
    cols = st.columns(2)
    with cols[0]:
        label_key = st.text_input(
            "Label Key", 
            key=f"{key_prefix}_label_key_input"
        )
    with cols[1]:
        label_value = st.text_input(
            "Label Value",
            key=f"{key_prefix}_label_value_input"
        )
    
    if st.button("Add Label", key=f"{key_prefix}_add_label"):
        if label_key and label_value:
            st.session_state[session_key][label_key] = label_value
            st.success("Label added successfully!")
        else:
            st.error("Both Label Key and Value are required!")
    
    labels_dict.update(st.session_state[session_key])
    
    st.write("Current Labels:")
    st.json(st.session_state[session_key])
    
    return labels_dict


def render_bucket_config(template_key="automation", bucket_key="bucket"):
    st.subheader(f"Bucket {bucket_key} Configuration" if bucket_key != "bucket" else "Automation Bucket Configuration")

    session_key = f"{template_key}_{bucket_key}_labels"
    if session_key not in st.session_state:
        st.session_state[session_key] = {}
    
    if template_key not in config_template:
        config_template[template_key] = {}
    if bucket_key not in config_template[template_key]:
        config_template[template_key][bucket_key] = {
            "description": "",
            "location": "",
            "prefix": "",
            "storage_class": "STANDARD",
            "uniform_bucket_level_access": False,
            "versioning": False,
            "labels": {},
            "iam": {},
            "iam_bindings": {}
        }
    
    bucket = config_template[template_key][bucket_key]
    key_prefix = f"{template_key}_{bucket_key}_"

    bucket["description"] = st.text_input(
        "Bucket Description",
        bucket.get("description", ""),
        key=f"{key_prefix}description"
    )
    
    bucket["location"] = st.text_input(
        "Bucket Location",
        bucket.get("location", ""),
        key=f"{key_prefix}location"
    )
    
    bucket["prefix"] = st.text_input(
        "Bucket Prefix",
        bucket.get("prefix", ""),
        key=f"{key_prefix}prefix"
    )
    
    bucket["storage_class"] = st.selectbox(
        "Storage Class",
        ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"],
        index=["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"].index(
            bucket.get("storage_class", "STANDARD")
        ),
        key=f"{key_prefix}storage_class"
    )
    
    bucket["uniform_bucket_level_access"] = st.checkbox(
        "Uniform Bucket Level Access",
        bucket.get("uniform_bucket_level_access", False),
        key=f"{key_prefix}ubla"
    )
    
    bucket["versioning"] = st.checkbox(
        "Enable Versioning",
        bucket.get("versioning", False),
        key=f"{key_prefix}versioning"
    )
    
    bucket["labels"] = render_labels(bucket.get("labels", {}), key_prefix)
    
    st.write("Current Labels:")
    st.json(bucket["labels"])

    bucket["iam"] = render_iam_config(
        f"{key_prefix}iam",
        bucket.get("iam", {})
    )
    existing_roles = get_existing_roles(bucket.get("iam", {}))
    bindings = render_iam_bindings(
        existing_roles,
        key_prefix
    )
    bucket["iam_bindings"] = bindings.get("standard", {})
    bucket["iam_bindings_additive"] = bindings.get("additive", {})

    if bucket_key != "bucket":
        if st.button("Remove Bucket", key=f"{key_prefix}remove"):
            config_template[template_key].pop(bucket_key, None)
            if session_key in st.session_state:
                st.session_state.pop(session_key)

def validate_id(id):
    return re.match(r"^[a-z0-9-]+$", id) is not None

def render_dynamic_schema(key, title):
    st.subheader(title)

    if key not in st.session_state:
        st.session_state[key] = {}

    new_id = st.text_input(f"Enter {title} ID", key=f"new_{key}_id", help="Only lowercase letters, numbers, and hyphens are allowed.")

    new_values = st.text_area(
        f"Enter {title} values (comma-separated):",
        key=f"new_{key}_values",
        help="Enter values as a comma-separated list.",
    )

    if st.button(f"Add {title}", key=f"add_{key}"):
        if new_id and validate_id(new_id):
            if new_id not in st.session_state[key]:
                values_list = [v.strip() for v in new_values.split(",") if v.strip()]
                st.session_state[key][new_id] = values_list
                st.success(f"{title} '{new_id}' added!")
            else:
                st.error(f"{title} ID '{new_id}' already exists!")
        else:
            st.error("Please enter a valid ID (lowercase letters, numbers, and hyphens only).")

    for entry_id, entry_values in st.session_state[key].items():
        st.write(f"{title} ID: {entry_id}")
        st.write(f"Values: {', '.join(entry_values)}")

        if st.button(f"Remove {entry_id}", key=f"remove_{key}_{entry_id}"):
            del st.session_state[key][entry_id]
            return

def render_service_accounts():
    st.subheader("Service Accounts")
    if "service_accounts" not in st.session_state:
        st.session_state.service_accounts = {}

    new_id = st.text_input("Enter Service Account ID", key="new_service_account_id", help="Only lowercase letters, numbers, and hyphens are allowed.")

    if st.button("Generate Service Account", key="generate_service_account"):
        if new_id and new_id not in st.session_state.service_accounts:
            import re
            if re.match(r"^[a-z0-9-]+$", new_id):
                st.session_state.service_accounts[new_id] = {
                    "description": "",
                    "iam": {},
                    "iam_bindings": {},
                    "iam_bindings_additive": {},
                    "iam_billing_roles": {},
                    "iam_folder_roles": {},
                    "iam_organization_roles": {},
                    "iam_project_roles": {},
                    "iam_sa_roles": {},
                    "iam_storage_roles": {}
                }
                st.success(f"Service Account '{new_id}' created!")
            else:
                st.error("Invalid Service Account ID. Only lowercase letters, numbers, and hyphens are allowed.")
        elif new_id in st.session_state.service_accounts:
            st.error("Service Account ID already exists!")
        else:
            st.error("Please enter a valid Service Account ID.")

    for sa_id, sa in st.session_state.service_accounts.items():
        st.write(f"Service Account: {sa_id}")
        sa["description"] = st.text_input(f"Description for {sa_id}", sa["description"], key=f"sa_desc_{sa_id}")

        st.write("IAM Configuration")
        sa["iam"] = render_iam_config(f"sa_iam_{sa_id}", sa.get("iam", {}))

        st.write("IAM Bindings")
        existing_roles = get_existing_roles(sa.get("iam", {}))
        iam_bindings = render_iam_bindings(existing_roles, f"sa_iam_bindings_{sa_id}")
        sa["iam_bindings"] = iam_bindings.get("standard", {})
        sa["iam_bindings_additive"] = iam_bindings.get("additive", {})

        st.write("IAM Billing Roles")
        sa["iam_billing_roles"] = render_dynamic_schema(f"sa_iam_billing_roles_{sa_id}", "IAM Billing Roles")

        st.write("IAM Folder Roles")
        sa["iam_folder_roles"] = render_dynamic_schema(f"sa_iam_folder_roles_{sa_id}", "IAM Folder Roles")

        st.write("IAM Organization Roles")
        sa["iam_organization_roles"] = render_dynamic_schema(f"sa_iam_organization_roles_{sa_id}", "IAM Organization Roles")

        st.write("IAM Project Roles")
        sa["iam_project_roles"] = render_dynamic_schema(f"sa_iam_project_roles_{sa_id}", "IAM Project Roles")

        st.write("IAM Service Account Roles")
        sa["iam_sa_roles"] = render_dynamic_schema(f"sa_iam_sa_roles_{sa_id}", "IAM Service Account Roles")

        st.write("IAM Storage Roles")
        sa["iam_storage_roles"] = render_dynamic_schema(f"sa_iam_storage_roles_{sa_id}", "IAM Storage Roles")
                
        if st.button(f"Remove Service Account {sa_id}", key=f"remove_sa_{sa_id}"):
            del st.session_state.service_accounts[sa_id]
            return

    config_template["automation"]["service_accounts"] = {
        sa_id: {
            "description": sa["description"],
            "iam": sa["iam"],
            "iam_bindings": sa["iam_bindings"],
            "iam_bindings_additive": sa["iam_bindings_additive"],
            "iam_billing_roles": sa["iam_billing_roles"],
            "iam_folder_roles": sa["iam_folder_roles"],
            "iam_organization_roles": sa["iam_organization_roles"],
            "iam_project_roles": sa["iam_project_roles"],
            "iam_sa_roles": sa["iam_sa_roles"],
            "iam_storage_roles": sa["iam_storage_roles"]
        }
        for sa_id, sa in st.session_state.service_accounts.items()
    }

def render_iam_roles(key, roles_data):
    st.subheader(f"IAM Roles Configuration for {key}")

    if key not in st.session_state:
        st.session_state[key] = roles_data

    new_role_key = st.text_input(
        "Add new role key (only lowercase letters, numbers, and hyphens):",
        key=f"new_role_key_{key}",
    )

    if st.button("Add Role", key=f"add_role_{key}"):
        if new_role_key:
            if not new_role_key.islower() or not new_role_key.replace("-", "").isalnum():
                st.error("Role key must contain only lowercase letters, numbers, and hyphens!")
            else:
                if new_role_key not in st.session_state[key]:
                    st.session_state[key][new_role_key] = []
                    st.success(f"Added new role: {new_role_key}")
                else:
                    st.error("Role key already exists!")
        else:
            st.error("Role key cannot be empty!")

    for role_key, role_values in st.session_state[key].items():
        st.write(f"Role: {role_key}")
        new_values = st.text_area(
            f"Edit values for {role_key} (comma-separated):",
            value=", ".join(role_values),
            key=f"edit_values_{role_key}_{key}",
            height=50,
        )
        st.session_state[key][role_key] = [v.strip() for v in new_values.split(",") if v.strip()]

    return st.session_state[key]

def render_string_inputs():
    st.header("Billing Account Configuration")
    config_template["billing_account"] = st.text_input("Billing Account", config_template.get("billing_account", ""))
    st.header("Name Configuration")
    config_template["name"] = st.text_input("Name", config_template.get("name", ""))
    st.header("Parent Configuration")
    config_template["parent"] = st.text_input("Parent", config_template.get("parent", ""))
    st.header("Prefix Configuration")
    config_template["prefix"] = st.text_input("Prefix", config_template.get("prefix", ""))

def render_string_array(key="billing_budgets", label="Billing Budgets"):
    st.subheader(label)
    
    if key not in st.session_state:
        st.session_state[key] = []
    
    new_budget = st.text_input(f"Add new {label[:-1]}", key=f"new_{key}")
    
    if st.button(f"Add {label[:-1]}", key=f"add_{key}"):
        if not new_budget:
            st.error("Budget value cannot be empty!")
        elif new_budget in st.session_state[key]:
            st.error("This budget already exists!")
        else:
            st.session_state[key].append(new_budget)
    
    if st.session_state[key]:
        st.write(f"Current {label}:")
        remove_cols = st.columns(len(st.session_state[key]))
        for i, (budget, col) in enumerate(zip(st.session_state[key], remove_cols)):
            with col:
                if st.button(f"❌ {budget}", key=f"remove_{key}_{i}"):
                    st.session_state[key].pop(i)
                    st.rerun()
    else:
        st.info(f"No {label.lower()} configured")
    
    return st.session_state[key]

def render_buckets():
    st.header("Buckets Configuration")
    
    if "buckets" not in config_template:
        config_template["buckets"] = {}
    
    if "buckets" not in st.session_state:
        st.session_state.buckets = config_template["buckets"].copy()
    
    with st.container(border=True):
        new_bucket_name = st.text_input(
            "New Bucket Name",
            key="new_bucket_input",
            help="Lowercase letters, numbers and hyphens only"
        )
        
        if st.button("➕ Add Bucket", key="add_bucket_btn"):
            if not new_bucket_name:
                st.error("Name is required")
            elif not re.match(r"^[a-z0-9-]+$", new_bucket_name):
                st.error("Only lowercase letters, numbers and hyphens allowed")
            elif new_bucket_name in st.session_state.buckets:
                st.error("Bucket already exists")
            else:
                new_bucket = {
                    "description": "",
                    "location": "",
                    "prefix": "",
                    "storage_class": "STANDARD",
                    "uniform_bucket_level_access": False,
                    "versioning": False,
                    "labels": {},
                    "iam": {},
                    "iam_bindings": {}
                }
                st.session_state.buckets[new_bucket_name] = new_bucket


    if not st.session_state.buckets:
        st.info("No buckets configured")
    else:
        for bucket_name in list(st.session_state.buckets.keys()):
            with st.expander(f"📦 {bucket_name}", expanded=True):
                bucket = st.session_state.buckets[bucket_name]
                
                cols = st.columns(2)
                with cols[0]:
                    bucket["description"] = st.text_input(
                        "Description",
                        bucket.get("description", ""),
                        key=f"desc_{bucket_name}"
                    )
                    bucket["location"] = st.text_input(
                        "Location",
                        bucket.get("location", ""),
                        key=f"loc_{bucket_name}"
                    )
                with cols[1]:
                    bucket["prefix"] = st.text_input(
                        "Prefix",
                        bucket.get("prefix", ""),
                        key=f"prefix_{bucket_name}"
                    )
                    bucket["storage_class"] = st.selectbox(
                        "Storage Class",
                        ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"],
                        index=["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"].index(
                            bucket.get("storage_class", "STANDARD")
                        ),
                        key=f"storage_{bucket_name}"
                    )
                
                bucket["uniform_bucket_level_access"] = st.checkbox(
                    "Uniform Bucket Level Access",
                    bucket.get("uniform_bucket_level_access", False),
                    key=f"ubla_{bucket_name}"
                )
                bucket["versioning"] = st.checkbox(
                    "Enable Versioning",
                    bucket.get("versioning", False),
                    key=f"version_{bucket_name}"
                )

                st.divider()
                st.write("**Labels**")
                labels_key = f"bucket_labels_{bucket_name}"
                if labels_key not in st.session_state:
                    st.session_state[labels_key] = bucket.get("labels", {}).copy()
                
                cols = st.columns([1, 1, 2])
                with cols[0]:
                    label_key = st.text_input("Key", key=f"label_key_{bucket_name}")
                with cols[1]:
                    label_value = st.text_input("Value", key=f"label_val_{bucket_name}")
                with cols[2]:
                    st.write("")
                    if st.button("Add Label", key=f"add_label_{bucket_name}"):
                        if label_key and label_value:
                            st.session_state[labels_key][label_key] = label_value
                            bucket["labels"] = st.session_state[labels_key]
                
                st.write("Current Labels:")
                st.json(bucket.get("labels", {}))

                st.divider()
                st.write("**IAM Configuration**")
                bucket["iam"] = render_iam_config(
                    f"iam_{bucket_name}",
                    bucket.get("iam", {})
                )
                existing_roles = get_existing_roles(bucket.get("iam", {}))
                iam_bindings = render_iam_bindings(
                    existing_roles,
                    f"iam_bindings_{bucket_name}"
                )
                bucket["iam_bindings"] = iam_bindings.get("standard", {})
                bucket["iam_bindings_additive"] = iam_bindings.get("additive", {})

                st.divider()
                if st.button(
                    "🗑️ Remove Bucket",
                    key=f"remove_{bucket_name}",
                    type="primary",
                    use_container_width=True
                ):
                    del st.session_state.buckets[bucket_name]
                    config_template["buckets"].pop(bucket_name, None)
                    if labels_key in st.session_state:
                        del st.session_state[labels_key]
    
    config_template["buckets"] = st.session_state.buckets.copy()

def render_contacts():
    st.header("Contacts")

    if "contacts" not in config_template:
        config_template["contacts"] = {}

    if "contacts" not in st.session_state:
        st.session_state.contacts = config_template["contacts"].copy()
    
    new_group = st.text_input(
        "New contact group name",
        help="Only lowercase letters, numbers, hyphens and underscores"
    )
    
    if st.button("Add group") and new_group:
        if not re.match(r"^[a-z0-9_-]+$", new_group):
            st.error("Invalid group name. Use lowercase letters, numbers, hyphens and underscores")
        elif new_group in st.session_state.contacts:
            st.error("Group already exists")
        else:
            st.session_state.contacts[new_group] = []


    for group_name in list(st.session_state.contacts.keys()):
        st.write(f"Group: {group_name}")
        
        new_contact = st.text_input(
            f"Add new contact to {group_name}",
            key=f"new_contact_{group_name}"
        )
        
        if st.button(f"Add to {group_name}", key=f"add_{group_name}"):
            if new_contact:
                st.session_state.contacts[group_name].append(new_contact)
        
        st.write("Current contacts:")
        for i, contact in enumerate(st.session_state.contacts[group_name]):
            cols = st.columns([4, 1])
            cols[0].write(contact)
            if cols[1].button("Remove", key=f"remove_{group_name}_{i}"):
                st.session_state.contacts[group_name].pop(i)
                st.rerun()
                        
        if st.button(f"Remove group {group_name}", key=f"remove_group_{group_name}"):
            del st.session_state.contacts[group_name]
            st.rerun()

    if "contacts" not in config_template:
        config_template["contacts"] = {}    

    config_template["contacts"] = st.session_state.contacts.copy()

def render_project_iam():
    st.subheader("IAM Configuration")
    config_template["iam"] = render_iam_config("iam", config_template.get("iam", {}))

    st.subheader("IAM Bindings Configuration")
    existing_roles = get_existing_roles(config_template.get("iam", {}))
    iam_bindigs = render_iam_bindings(existing_roles, "iam")
    config_template["iam_bindings"] = iam_bindigs.get("standard", {})
    config_template["iam_bindings_additive"] = iam_bindigs.get("additive", {})

def render_automation():
    st.header("Automation Configuration")
    
    if "automation" not in config_template:
        config_template["automation"] = {
            "project": "",
            "bucket": {},
            "service_accounts": {}
        }
    
    generate_automation = st.checkbox(
        "Generate Automation", 
        value=bool(config_template["automation"].get("project")),
        key="generate_automation"
    )
    
    if generate_automation:
        config_template["automation"]["project"] = st.text_input(
            "Project Name", 
            config_template["automation"].get("project", ""),
            key="automation_project"
        )
        
        render_bucket_config("automation", "bucket")

        render_service_accounts()

    if generate_automation and config_template["automation"]["project"] == "":
        return "no"
    else:
        return "yes"
    

def render_iam_by_principals():
    st.subheader("IAM Bindings by Principals")
    
    if "iam_by_principals" not in config_template:
        config_template["iam_by_principals"] = {}
    

    if "iam_by_principals" not in st.session_state:
        st.session_state.iam_by_principals = config_template["iam_by_principals"].copy()
    
    with st.container(border=True):
        st.write("Add New Principal")
        cols = st.columns([3, 1])
        with cols[0]:
            new_principal = st.text_input(
                "Principal (domain:|group:|serviceAccount:|user:|principal:|principalSet:| or lowercase letter)",
                key="new_principal_input",
                help="Format: domain:|group:|serviceAccount:|user:|principal:|principalSet:|[a-z]..."
            )
        with cols[1]:
            new_role = st.text_input(
                "Role (must start with roles/)",
                key="new_role_input",
                value="roles/"
            )
        
        if st.button("Add Binding", key="add_principal_binding"):
            if not new_principal:
                st.error("Principal is required!")
            elif not re.match(r"^(?:domain:|group:|serviceAccount:|user:|principal:|principalSet:|[a-z])", new_principal):
                st.error("Invalid principal format!")
            elif not new_role.startswith("roles/"):
                st.error("Role must start with 'roles/'")
            else:
                if new_principal not in st.session_state.iam_by_principals:
                    st.session_state.iam_by_principals[new_principal] = []
                
                if new_role not in st.session_state.iam_by_principals[new_principal]:
                    st.session_state.iam_by_principals[new_principal].append(new_role)
                    st.success(f"Added {new_role} to {new_principal}")
                else:
                    st.error("This role already exists for this principal!")
    
    if not st.session_state.iam_by_principals:
        st.info("No principal bindings configured yet")
    else:
        for principal in list(st.session_state.iam_by_principals.keys()):
            with st.expander(f"Principal: {principal}", expanded=True):
                st.write("Assigned Roles:")
                roles = st.session_state.iam_by_principals[principal]
                
                if not roles:
                    st.info("No roles assigned")
                else:
                    for role in roles:
                        cols = st.columns([4, 1])
                        cols[0].write(role)
                        if cols[1].button("Remove", key=f"remove_{principal}_{role}"):
                            st.session_state.iam_by_principals[principal].remove(role)
                            if not st.session_state.iam_by_principals[principal]:
                                del st.session_state.iam_by_principals[principal]
                            st.rerun()
                
                new_role = st.text_input(
                    f"Add new role to {principal}",
                    value="roles/",
                    key=f"add_role_to_{principal}"
                )
                
                if st.button("Add Role", key=f"add_role_btn_{principal}"):
                    if not new_role.startswith("roles/"):
                        st.error("Role must start with 'roles/'")
                    elif new_role in st.session_state.iam_by_principals[principal]:
                        st.error("Role already exists for this principal!")
                    else:
                        st.session_state.iam_by_principals[principal].append(new_role)
                        st.rerun()
                
                if st.button(f"Remove Principal {principal}", key=f"remove_principal_{principal}"):
                    del st.session_state.iam_by_principals[principal]
                    st.rerun()
    
    config_template["iam_by_principals"] = st.session_state.iam_by_principals.copy()

def render_org_policies():
    st.subheader("Organization Policies Configuration")
    
    if "org_policies" not in config_template:
        config_template["org_policies"] = {}
    
    if "org_policies" not in st.session_state:
        st.session_state.org_policies = config_template["org_policies"].copy()
    
    with st.container(border=True):
        st.write("Add New Policy")
        new_policy_key = st.text_input(
            "Policy ID (must start with lowercase letters then \\ and then anything)",
            key="new_policy_input",
            help="Example: mypolicy\\..."
        )
        
        if st.button("Add Policy", key="add_policy_btn"):
            if not new_policy_key:
                st.error("Policy ID is required!")
            elif not re.match(r"^[a-z]+\\.", new_policy_key):
                st.error("Policy ID must start with lowercase letters and end with dot!")
            elif new_policy_key in st.session_state.org_policies:
                st.error("Policy already exists!")
            else:
                st.session_state.org_policies[new_policy_key] = {
                    "inherit_from_parent": False,
                    "reset": False,
                    "rules": []
                }
                st.rerun()
    
    if not st.session_state.org_policies:
        st.info("No organization policies configured")
    else:
        for policy_key in list(st.session_state.org_policies.keys()):
            policy = st.session_state.org_policies[policy_key]
            
            with st.expander(f"Policy: {policy_key}", expanded=True):
                cols = st.columns(2)
                with cols[0]:
                    policy["inherit_from_parent"] = st.checkbox(
                        "Inherit from parent",
                        value=policy["inherit_from_parent"],
                        key=f"{policy_key}_inherit"
                    )
                with cols[1]:
                    policy["reset"] = st.checkbox(
                        "Reset",
                        value=policy["reset"],
                        key=f"{policy_key}_reset"
                    )
                
                st.subheader("Rules")
                if st.button("Add New Rule", key=f"add_rule_{policy_key}"):
                    policy["rules"].append({
                        "allow": {"all": False, "values": []},
                        "deny": {"all": False, "values": []},
                        "enforce": True,
                        "condition": {
                            "description": "",
                            "expression": "",
                            "location": "",
                            "title": ""
                        }
                    })
                    st.rerun()
                
                for rule_idx, rule in enumerate(policy["rules"]):
                    with st.container(border=True):
                        cols = st.columns([4, 1])
                        with cols[1]:
                            if st.button("🗑️", key=f"del_rule_{policy_key}_{rule_idx}"):
                                policy["rules"].pop(rule_idx)
                                st.rerun()
                                break
                        
                        tab_allow, tab_deny = st.tabs(["Allow", "Deny"])
                        
                        with tab_allow:
                            rule["allow"]["all"] = st.checkbox(
                                "Allow All",
                                value=rule["allow"]["all"],
                                key=f"allow_all_{policy_key}_{rule_idx}"
                            )
                            if not rule["allow"]["all"]:
                                allow_values = st.text_area(
                                    "Allowed Values (one per line)",
                                    value="\n".join(rule["allow"]["values"]),
                                    key=f"allow_values_{policy_key}_{rule_idx}"
                                )
                                rule["allow"]["values"] = [v.strip() for v in allow_values.split("\n") if v.strip()]
                        
                        with tab_deny:
                            rule["deny"]["all"] = st.checkbox(
                                "Deny All",
                                value=rule["deny"]["all"],
                                key=f"deny_all_{policy_key}_{rule_idx}"
                            )
                            if not rule["deny"]["all"]:
                                deny_values = st.text_area(
                                    "Denied Values (one per line)",
                                    value="\n".join(rule["deny"]["values"]),
                                    key=f"deny_values_{policy_key}_{rule_idx}"
                                )
                                rule["deny"]["values"] = [v.strip() for v in deny_values.split("\n") if v.strip()]
                        
                        rule["enforce"] = st.checkbox(
                            "Enforce",
                            value=rule["enforce"],
                            key=f"enforce_{policy_key}_{rule_idx}"
                        )
                        
                        st.subheader("Condition")
                        rule["condition"]["title"] = st.text_input(
                            "Title",
                            value=rule["condition"]["title"],
                            key=f"cond_title_{policy_key}_{rule_idx}"
                        )
                        rule["condition"]["description"] = st.text_input(
                            "Description",
                            value=rule["condition"]["description"],
                            key=f"cond_desc_{policy_key}_{rule_idx}"
                        )
                        rule["condition"]["expression"] = st.text_area(
                            "Expression",
                            value=rule["condition"]["expression"],
                            key=f"cond_expr_{policy_key}_{rule_idx}"
                        )
                        rule["condition"]["location"] = st.text_input(
                            "Location",
                            value=rule["condition"]["location"],
                            key=f"cond_loc_{policy_key}_{rule_idx}"
                        )
                
                if st.button("Remove Policy", key=f"remove_policy_{policy_key}"):
                    del st.session_state.org_policies[policy_key]
                    st.rerun()
    
    config_template["org_policies"] = st.session_state.org_policies.copy()

def render_service_accounts():
    st.subheader("Service Accounts Configuration")
    
    if "service_accounts" not in config_template:
        config_template["service_accounts"] = {}
    
    if "service_accounts" not in st.session_state:
        st.session_state.service_accounts = config_template["service_accounts"].copy()
    
    with st.container(border=True):
        st.write("Add New Service Account")
        new_sa_id = st.text_input(
            "Service Account ID",
            help="Lowercase letters, numbers and hyphens only",
            key="new_sa_id_input"
        )
        
        if st.button("Add Service Account", key="add_sa_btn"):
            if not new_sa_id:
                st.error("Service Account ID is required!")
            elif not re.match(r"^[a-z0-9-]+$", new_sa_id):
                st.error("Only lowercase letters, numbers and hyphens allowed!")
            elif new_sa_id in st.session_state.service_accounts:
                st.error("Service Account ID already exists!")
            else:
                st.session_state.service_accounts[new_sa_id] = {
                    "display_name": "",
                    "iam_self_roles": [],
                    "iam_project_roles": {}
                }
                st.rerun()
    
    if not st.session_state.service_accounts:
        st.info("No service accounts configured")
    else:
        for sa_id in list(st.session_state.service_accounts.keys()):
            sa = st.session_state.service_accounts[sa_id]
            
            with st.expander(f"Service Account: {sa_id}", expanded=True):
                sa["display_name"] = st.text_input(
                    "Display Name",
                    value=sa.get("display_name", ""),
                    key=f"sa_display_name_{sa_id}"
                )
                
                st.subheader("IAM Self Roles")
                new_self_role = st.text_input(
                    "Add new self role",
                    key=f"new_self_role_{sa_id}"
                )
                
                if st.button("Add Self Role", key=f"add_self_role_{sa_id}"):
                    if new_self_role and new_self_role not in sa["iam_self_roles"]:
                        sa["iam_self_roles"].append(new_self_role)
                        st.rerun()
                
                st.write("Current Self Roles:")
                if not sa["iam_self_roles"]:
                    st.info("No self roles assigned")
                else:
                    for role_idx, role in enumerate(sa["iam_self_roles"]):
                        cols = st.columns([4, 1])
                        cols[0].write(role)
                        if cols[1].button("Remove", key=f"remove_self_role_{sa_id}_{role_idx}"):
                            sa["iam_self_roles"].pop(role_idx)
                            st.rerun()
                            break
                
                st.subheader("IAM Project Roles")
                sa["iam_project_roles"] = render_dynamic_schema(
                    key=f"sa_{sa_id}_project_roles",
                    title="Project Roles",
                )
                
                if st.button("Remove Service Account", key=f"remove_sa_{sa_id}"):
                    del st.session_state.service_accounts[sa_id]
                    st.rerun()
    
    config_template["service_accounts"] = st.session_state.service_accounts.copy()

def render_service_encryption_key_ids():
    st.subheader("Service Encryption Key IDs Configuration")
    
    if "service_encryption_key_ids" not in config_template:
        config_template["service_encryption_key_ids"] = {}
    
    if "service_encryption_key_ids" not in st.session_state:
        st.session_state.service_encryption_key_ids = config_template["service_encryption_key_ids"].copy()
    
    with st.container(border=True):
        st.write("Add New Service Configuration")
        new_service = st.text_input(
            "Service Name (must end with .googleapis.com)",
            help="Example: compute.googleapis.com",
            key="new_service_input_for_key_ids"
        )
        
        if st.button("Add Service", key="add_service_btn_for_key_ids"):
            if not new_service:
                st.error("Service name is required!")
            elif not re.match(r"^[a-z-]+\.googleapis\.com$", new_service):
                st.error("Service name must end with .googleapis.com!")
            elif new_service in st.session_state.service_encryption_key_ids:
                st.error("Service already exists!")
            else:
                st.session_state.service_encryption_key_ids[new_service] = []
                st.rerun()
    
    if not st.session_state.service_encryption_key_ids:
        st.info("No service encryption keys configured")
    else:
        for service in list(st.session_state.service_encryption_key_ids.keys()):
            key_ids = st.session_state.service_encryption_key_ids[service]
            
            with st.expander(f"Service: {service}", expanded=True):
                new_key_id = st.text_input(
                    "Add new encryption key ID",
                    key=f"new_key_id_{service}"
                )
                
                if st.button("Add Key ID", key=f"add_key_{service}"):
                    if new_key_id and new_key_id not in key_ids:
                        key_ids.append(new_key_id)
                        st.rerun()
                    elif new_key_id in key_ids:
                        st.error("Key ID already exists for this service!")
                
                st.write("Current Key IDs:")
                if not key_ids:
                    st.info("No key IDs configured for this service")
                else:
                    for idx, key_id in enumerate(key_ids):
                        cols = st.columns([4, 1])
                        cols[0].write(key_id)
                        if cols[1].button("Remove", key=f"remove_key_{service}_{idx}"):
                            key_ids.pop(idx)
                            st.rerun()
                            break
                
                if st.button("Remove Service", key=f"remove_service_{service}"):
                    del st.session_state.service_encryption_key_ids[service]
                    st.rerun()
    
    config_template["service_encryption_key_ids"] = st.session_state.service_encryption_key_ids.copy()

def render_services():
    st.subheader("Google APIs Services Configuration")
    
    if "services" not in config_template:
        config_template["services"] = []
    
    if "services" not in st.session_state:
        st.session_state.services = config_template["services"].copy()

    with st.container(border=True):
        new_service = st.text_input(
            "Add new Google API service",
            help="Must end with .googleapis.com (e.g., compute.googleapis.com)",
            key="new_service_input"
        )
        
        if st.button("Add Service", key="add_service_btn"):
            if not new_service:
                st.error("Service name is required!")
            elif not re.match(r"^[a-z-]+\.googleapis\.com$", new_service):
                st.error("Service must be in format: [name].googleapis.com")
            elif new_service in st.session_state.services:
                st.error("Service already exists in list!")
            else:
                st.session_state.services.append(new_service)
                st.rerun()
    
    st.write("Enabled Services:")
    if not st.session_state.services:
        st.info("No services configured yet")
    else:
        for i, service in enumerate(st.session_state.services):
            cols = st.columns([4, 1])
            cols[0].write(service)
            if cols[1].button("Remove", key=f"remove_service_{i}"):
                st.session_state.services.pop(i)
                st.rerun()
                break
    
    config_template["services"] = st.session_state.services.copy()

def render_shared_vpc_host():
    st.header("Shared VPC Host Configuration")

    if "shared_vpc_host_config" not in config_template:
        config_template["shared_vpc_host_config"] = {
            "enabled": False,
            "service_projects": [],
        }

    if "shared_vpc_host_config" not in st.session_state:
        st.session_state.shared_vpc_host_config = config_template["shared_vpc_host_config"].copy()

    if "enabled" not in st.session_state.shared_vpc_host_config:
        st.session_state.shared_vpc_host_config["enabled"] = False

    st.session_state.shared_vpc_host_config["enabled"] = st.checkbox(
        "Enable Shared VPC Host",
        value=st.session_state.shared_vpc_host_config["enabled"],
    )

    if st.session_state.shared_vpc_host_config["enabled"]:
        st.session_state.shared_vpc_host_config["service_projects"] = render_string_array(
            key="service_projects",
            label="Service Projects",
        )

    else:
        st.session_state.shared_vpc_host_config["service_projects"] = []


    config_template["shared_vpc_host_config"] = st.session_state.shared_vpc_host_config.copy()

def render_shared_vpc_service_config():

    st.subheader("Shared VPC Service Configuration")

    if "shared_vpc_service_config" not in config_template:
        config_template["shared_vpc_service_config"] = {
            "host_project": "",
            "network_users": [],
            "service_agent_iam": {},
            "service_agent_subnet_iam": {},
            "service_iam_grants": [],
            "network_subnet_users": {},
        }

    if "shared_vpc_service_config" not in st.session_state:
        st.session_state.shared_vpc_service_config = config_template["shared_vpc_service_config"].copy()

    st.session_state.shared_vpc_service_config["host_project"] = st.text_input(
        "Host Project",
        value=st.session_state.shared_vpc_service_config["host_project"],
    )

    st.session_state.shared_vpc_service_config["network_users"] = render_string_array(
        key="network_users",
        label="Network Users",
    )

    st.session_state.shared_vpc_service_config["service_agent_iam"] = render_dynamic_schema(
        key="service_agent_iam",
        title="Service Agent IAM",
    )

    st.session_state.shared_vpc_service_config["service_agent_subnet_iam"] = render_dynamic_schema(
        key="service_agent_subnet_iam",
        title="Service Agent Subnet IAM",
    )

    st.session_state.shared_vpc_service_config["service_iam_grants"] = render_string_array(
        key="service_iam_grants",
        label="Service IAM Grants",
    )

    st.session_state.shared_vpc_service_config["network_subnet_users"] = render_dynamic_schema(
        key="network_subnet_users",
        title="Network Subnet Users",
    )

    config_template["shared_vpc_service_config"] = st.session_state.shared_vpc_service_config.copy()


def render_vpc_sc():
    st.header("VPC Service Controls Configuration")

    generate_vpc_sc = st.checkbox(
        "Generate VPC Service Controls", 
        value=bool(config_template["automation"].get("project")),
        key="generate_vpc_sc"
    )

    if generate_vpc_sc:

        if "vpc_sc" not in config_template:
            config_template["vpc_sc"] = {
                "perimeter_name": "",
                "perimeter_bridges": [],
                "is_dry_run": False
            }

        if "vpc_sc" not in st.session_state:
            st.session_state.vpc_sc = config_template["vpc_sc"].copy()
            st.session_state.vpc_sc["perimeter_bridges"] = st.session_state.vpc_sc.get("perimeter_bridges", [])
        
        st.session_state.vpc_sc["perimeter_name"] = st.text_input(
            "Perimeter Name*",
            value=st.session_state.vpc_sc.get("perimeter_name", ""),
            key="vpc_sc_perimeter_name",
            help="Required field"
        )
        
        st.write("Perimeter Bridges")
        new_bridge = st.text_input(
            "Add new bridge perimeter",
            key="new_perimeter_bridge"
        )
        
        if st.button("Add Bridge", key="add_bridge_btn"):
            if new_bridge and new_bridge not in st.session_state.vpc_sc["perimeter_bridges"]:
                st.session_state.vpc_sc["perimeter_bridges"].append(new_bridge)
                st.rerun()

        if st.session_state.vpc_sc["perimeter_bridges"]:
            st.write("Current Bridges:")
            for i, bridge in enumerate(st.session_state.vpc_sc["perimeter_bridges"]):
                cols = st.columns([4, 1])
                cols[0].write(bridge)
                if cols[1].button("Remove", key=f"remove_bridge_{i}"):
                    st.session_state.vpc_sc["perimeter_bridges"].pop(i)
                    st.rerun()
        else:
            st.info("No perimeter bridges configured")
        
        st.session_state.vpc_sc["is_dry_run"] = st.checkbox(
            "Dry Run Mode",
            value=st.session_state.vpc_sc.get("is_dry_run", False),
            key="vpc_sc_dry_run",
            help="Enable to test configuration without enforcement"
        )
        
        if not st.session_state.vpc_sc["perimeter_name"]:
            st.error("Perimeter name is required!")
            return False
        
        config_template["vpc_sc"] = st.session_state.vpc_sc.copy()
        return True
    return True

st.title("Project Factory Frontend")

automation_savable = render_automation()

render_string_inputs()

render_string_array()

render_buckets()

render_contacts()

render_project_iam()

render_iam_by_principals()

config_template["labels"] = render_labels(config_template.get("labels", {}), "labels")

render_string_array("metric_scopes", "Metric Scopes")

render_org_policies()

render_service_accounts()

render_service_encryption_key_ids()

render_services()

render_shared_vpc_host()

render_shared_vpc_service_config()

render_dynamic_schema(
    key="tag_bindings",
    title="Tag Bindings",
)

savable = render_vpc_sc()


if st.button("Save Config"):
    if automation_savable == "no":
        st.error("A Project Name kötelező!")
    elif not can_save_config(config_template["automation"]["bucket"].get("iam_bindings", {})):
        st.error("Invalid IAM Bindings configuration!")
    elif not savable:
        st.error("Invalid VPC SC configuration!")
    else:
        save_yaml(config_template)

if st.button("Reset Config"):
    st.session_state.clear()
    st.rerun() 
