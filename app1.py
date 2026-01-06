# Children - Mobile Friendly
st.markdown('<div class="sub-header">👨‍👩‍👧‍👦 Children</div>', unsafe_allow_html=True)

# Display current children
for i, kid in enumerate(st.session_state.kids):
    st.markdown(f"**Child {i+1}:**")
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_name = st.text_input(f"Child {i+1} name", value=kid, key=f"kid_{i}", placeholder=f"Enter name")
        st.session_state.kids[i] = new_name
    with col_btn:
        if len(st.session_state.kids) > 1:
            if st.button("🗑️ Remove", key=f"rm_kid_{i}"):
                st.session_state.kids.pop(i)
                st.experimental_rerun()  # only rerun after button press

# Add new child section
st.markdown("**Add a new child**")
new_child_name = st.text_input("New child name", value="", key="new_kid_name", placeholder="Type name and tap 'Add'")
if st.button("➕ Add Child"):
    if new_child_name.strip():
        st.session_state.kids.append(new_child_name.strip())
        st.session_state.new_kid_name = ""  # reset input
        st.experimental_rerun()
