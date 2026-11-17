#FLM: GS: Stroke Live
#NOTE: Live (non-expanded) strokes on skeleton artwork per master: Luminous Symbols and Google Symbols presets.
# ----------------------------------------
# (C) Vassil Kateliev, 2020-2026 	(http://www.kateliev.com)
# (C) Karandash Type Foundry 		(http://www.karandash.eu)
# (C) TypeRig                		(http://www.typerig.com)
#-----------------------------------------
# PROJECT: Google Symbols - Variable Font (Google)
#-----------------------------------------

# No warranties. By using this you agree
# that you use it at your own risk!

# Same job as LS-Stroke-Expand.py / GS-Stroke-Expand.py, but nothing is
# expanded: every skeleton element gets a live stroke through its pen.
# FontLab keeps an element's brush/stroke weight in flShape.pen (QPen) width,
# verified in the app 2026-10-29 (a brush element of size 80 reads pen width 80).
#
# Per target layer, as in the expand scripts: a missing layer is created;
# a layer with its own shapes keeps them; an empty layer gets a copy of the
# source (Regular) skeleton.
#
# Optional style donor: an element already stroked by hand in FontLab. Its
# style (assignStyle) goes onto every element first, then the preset sets the
# pen weight, cap and join. Use it if the pen alone does not give the stroke
# engine you want (calligraphic brush angle, nib and the rest).

# Two stroke modes, picked in the dialog:
#  - Live: the skeleton stays, every element gets a pen stroke. Reversible,
#    the artwork remains editable, nothing is outlined.
#  - Static: the skeleton is expanded into an outline with the TypeRig pen
#    (typerig.core.objects.metapen), the same job as GS-Stroke-Expand.py.
#    The layer contents are REPLACED by the expanded result, so the skeleton
#    is gone afterwards. The style donor does not apply in this mode.

# - Dependencies -----------------
from __future__ import absolute_import, print_function
from collections import OrderedDict

import fontlab as fl6
from PythonQt import QtCore

from typerig.proxy.fl.gui import QtGui

from typerig.proxy.fl.objects.font import pFont
from typerig.proxy.fl.objects.glyph import eGlyph
from typerig.proxy.tr.objects.glyph import trGlyph

from typerig.core.objects.layer import Layer
from typerig.core.objects.shape import Shape
from typerig.core.objects.metapen import PenStroke, Nib, CAP_ROUND, CAP_BUTT, JOIN_ROUND, JOIN_MITER

from typerig.core.base.message import output

# - Init --------------------------------
app_name, app_version = 'GS | Stroke Live', '1.1'

# - Configuration ------------------------
source_layer_name = 'Regular'
filled_suffix = ' Filled'

# -- {master: stroke width}, same values as the expand scripts
master_widths = OrderedDict([	('Thin', 		28),
								('Regular', 	80),
								('Bold', 		126),
								('20pt', 		72),
								('48pt', 		60),
								('Weak', 		70),
								('Strong', 		106)])

# -- Presets: caps and joins of the expand scripts
LUMINOUS = 'Luminous Symbols'
GOOGLE = 'Google Symbols'

presets = {	LUMINOUS: {'cap': QtCore.Qt.RoundCap, 'join': QtCore.Qt.RoundJoin,
					   'cap_static': CAP_ROUND, 'join_static': JOIN_ROUND,
					   'filled': False, 'info': 'Round cap, round join; masters only'},
			GOOGLE:   {'cap': QtCore.Qt.FlatCap,  'join': QtCore.Qt.MiterJoin,
					   'cap_static': CAP_BUTT, 'join_static': JOIN_MITER,
					   'filled': True,  'info': 'Butt cap, miter join; masters + Filled layers'}}

# - Helpers ------------------------------
def find_or_add_layer(glyph, layer_name):
	'''Return the glyph's flLayer by name, creating an empty one if missing. (layer, created)'''
	for layer in glyph.fl.layers:
		if layer.name == layer_name:
			return layer, False

	new_layer = fl6.flLayer()
	new_layer.name = str(layer_name)
	glyph.fl.addLayer(new_layer)

	for layer in glyph.fl.layers:
		if layer.name == layer_name:
			return layer, True

	return None, True

def copy_skeleton(src_layer, dst_layer):
	'''Copy the source skeleton elements as independent clones, transforms and advance included.'''
	for shape in src_layer.shapes:
		clone = dst_layer.addShape(shape.cloneTopLevel())
		if clone is not None: clone.transform = shape.transform

	dst_layer.advanceWidth = src_layer.advanceWidth

def stroke_shapes(shapes, width, cap, join, donor=None):
	'''Give every element a live stroke. Groups are walked; glyph components are left alone.
	Returns the number of elements stroked.'''
	count = 0

	for shape in shapes:
		if len(shape.includesList):
			count += stroke_shapes(shape.includesList, width, cap, join, donor)
			continue

		if shape.isComponent or not len(shape.contours):
			continue

		if donor is not None:
			keep_transform = shape.transform # assignStyle may carry the donor transform
			shape.assignStyle(donor)
			shape.transform = keep_transform
		else:
			shape.brush = QtGui.QBrush() # No fill: a stroke only, as the expanded result

		pen = QtGui.QPen(shape.pen)
		pen.setStyle(QtCore.Qt.SolidLine)
		pen.setWidthF(float(width))
		pen.setCapStyle(cap)
		pen.setJoinStyle(join)
		shape.pen = pen
		shape.update()
		count += 1

	return count

def stroke_glyph(glyph, layer_widths, cap, join, donor=None):
	'''Apply live strokes to one glyph. Returns a list of report lines.'''
	report = []
	src_layer = glyph.fl.getLayerByName(source_layer_name)

	if src_layer is None:
		output(2, app_name, 'Glyph: {}; Source layer <{}> not found! Skipped.'.format(glyph.name, source_layer_name))
		return report

	for layer_name, width in layer_widths.items():
		layer, created = find_or_add_layer(glyph, layer_name)

		if layer is None:
			output(2, app_name, 'Glyph: {}; Could not create layer <{}>!'.format(glyph.name, layer_name))
			continue

		# - Prefer the layer's own skeleton; an empty layer takes the source one
		if not len(layer.shapes):
			copy_skeleton(src_layer, layer)
			origin = 'new, from {}'.format(source_layer_name) if created else 'from {}'.format(source_layer_name)
		else:
			origin = 'own'

		count = stroke_shapes(layer.shapes, width, cap, join, donor)
		report.append('{} {}u ({}, {} el.)'.format(layer_name, width, origin, count))

	return report

# - Static (expanded) strokes ------------
def expand_skeleton(skeleton, width, cap, join):
	'''Expand every contour of a core Layer skeleton with a circular nib of <width>.
	Returns a list of core Contours.'''
	nib = Nib.circle(width)
	expanded = []

	for shape in skeleton.shapes:
		for contour in shape.contours:
			segments = contour.segments

			if not len(segments):
				continue

			stroke = PenStroke(segments, nib, closed=contour.closed, method=0, cap=cap, join=join)

			# to_contours() gives separate contours: open paths 1, closed paths 2 (outer + inner)
			expanded.extend(stroke.expand().to_contours())

	return expanded

def expand_glyph(glyph, layer_widths, cap, join):
	'''Replace the skeleton of every target layer with an expanded outline.
	Same per-layer rules as stroke_glyph. Returns a list of report lines.'''
	report = []
	tr_glyph = trGlyph(glyph.fl)
	src_layer = tr_glyph.find_layer(source_layer_name)

	if src_layer is None:
		output(2, app_name, 'Glyph: {}; Source layer <{}> not found! Skipped.'.format(glyph.name, source_layer_name))
		return report

	source_skeleton = src_layer.eject() # FL-independent copy, taken before any layer is mounted

	for layer_name, width in layer_widths.items():
		tr_layer = tr_glyph.find_layer(layer_name)
		created = tr_layer is None

		if created:
			tr_layer = tr_glyph.add_layer(layer_name)

		if tr_layer is None:
			output(2, app_name, 'Glyph: {}; Could not create layer <{}>!'.format(glyph.name, layer_name))
			continue

		# - Prefer the layer's own skeleton; an empty layer takes the source one
		layer_skeleton = tr_layer.eject()

		if len(layer_skeleton.shapes):
			skeleton, origin = layer_skeleton, 'own'
		else:
			skeleton = source_skeleton
			origin = 'new, from {}'.format(source_layer_name) if created else 'from {}'.format(source_layer_name)

		contours = expand_skeleton(skeleton, width, cap, join)

		if not len(contours):
			output(1, app_name, 'Glyph: {}; Layer: {}; Nothing to expand!'.format(glyph.name, layer_name))
			continue

		new_layer = Layer([Shape(contours)],
						name=layer_name,
						width=skeleton.advance_width,
						height=skeleton.advance_height,
						anchors=skeleton.anchors,
						guidelines=skeleton.guidelines)

		tr_layer.mount(new_layer)
		report.append('{} {:g}u ({}, {} cnt.)'.format(layer_name, width, origin, len(contours)))

	return report

# - Interface -----------------------------
class dlg_stroke_live(QtGui.QDialog):
	def __init__(self):
		super(dlg_stroke_live, self).__init__()

		# - Init
		self.donor = None

		# - Group boxes
		self.box_mode = QtGui.QGroupBox('Stroke mode')
		self.box_widths = QtGui.QGroupBox('Stroke width per master')
		self.box_opt = QtGui.QGroupBox('Options')

		# - Mode radios
		self.rad_group_mode = QtGui.QButtonGroup()
		self.rad_live = QtGui.QRadioButton('Live stroke (pen)')
		self.rad_static = QtGui.QRadioButton('Static stroke (expanded)')
		self.rad_live.setChecked(True)

		self.rad_live.setToolTip('Keep the skeleton and give every element a live stroke through\nits pen: reversible, still editable, nothing outlined.')
		self.rad_static.setToolTip('Expand the skeleton into an outline with the TypeRig pen\n(the job of GS-Stroke-Expand.py). The layer contents are\nreplaced by the expanded result: the skeleton is gone.\nThe style donor does not apply here.')

		self.rad_group_mode.addButton(self.rad_live, 1)
		self.rad_group_mode.addButton(self.rad_static, 2)
		self.rad_live.toggled.connect(self.mode_changed)

		layout_mode = QtGui.QVBoxLayout()
		layout_mode.addWidget(self.rad_live)
		layout_mode.addWidget(self.rad_static)
		self.box_mode.setLayout(layout_mode)

		# - Widths
		layout_widths = QtGui.QGridLayout()
		self.spn_widths = OrderedDict()

		for row, (master_name, width) in enumerate(master_widths.items()):
			spn_width = QtGui.QDoubleSpinBox()
			spn_width.setRange(0., 1000.)
			spn_width.setDecimals(1)
			spn_width.setValue(width)
			spn_width.setToolTip('Stroke width for layer <{0}> (and <{0}{1}> for Google Symbols).'.format(master_name, filled_suffix))
			self.spn_widths[master_name] = spn_width

			layout_widths.addWidget(QtGui.QLabel(master_name),	row, 0, 1, 1)
			layout_widths.addWidget(spn_width,					row, 1, 1, 1)

		self.btn_reset = QtGui.QPushButton('Reset widths')
		self.btn_reset.setToolTip('Back to the widths of the expand scripts.')
		self.btn_reset.clicked.connect(self.reset_widths)
		layout_widths.addWidget(self.btn_reset, len(master_widths), 0, 1, 2)
		self.box_widths.setLayout(layout_widths)

		# - Options: style donor
		self.lbl_donor = QtGui.QLabel('Donor: none')
		self.btn_donor_set = QtGui.QPushButton('Set donor')
		self.btn_donor_clear = QtGui.QPushButton('Clear')

		self.btn_donor_set.setToolTip('Take the selected element of the active glyph (stroked by hand in FontLab)\nas the style donor: its style goes onto every element before the preset\nsets the pen weight, cap and join. Leave empty for the pen alone.')
		self.btn_donor_clear.setToolTip('Stroke with the pen alone (no fill).')
		self.btn_donor_set.clicked.connect(self.donor_set)
		self.btn_donor_clear.clicked.connect(self.donor_clear)

		layout_donor = QtGui.QGridLayout()
		layout_donor.addWidget(self.lbl_donor,			0, 0, 1, 2)
		layout_donor.addWidget(self.btn_donor_set,		1, 0, 1, 1)
		layout_donor.addWidget(self.btn_donor_clear,	1, 1, 1, 1)
		self.box_opt.setLayout(layout_donor)

		# - Run buttons
		self.btn_luminous = QtGui.QPushButton(LUMINOUS)
		self.btn_google = QtGui.QPushButton(GOOGLE)

		for button, preset_name in ((self.btn_luminous, LUMINOUS), (self.btn_google, GOOGLE)):
			button.setMinimumHeight(40)
			button.setToolTip('{}: {}.\nLive strokes on every selected glyph (or the active glyph if none are selected).'.format(preset_name, presets[preset_name]['info']))

		self.btn_luminous.clicked.connect(lambda: self.action_stroke(LUMINOUS))
		self.btn_google.clicked.connect(lambda: self.action_stroke(GOOGLE))

		# - Build layouts
		layout_main = QtGui.QVBoxLayout()
		layout_main.addWidget(self.box_mode)
		layout_main.addWidget(self.box_widths)
		layout_main.addWidget(self.box_opt)
		layout_main.addWidget(self.btn_luminous)
		layout_main.addWidget(self.btn_google)
		layout_main.addStretch()

		# - Set widget
		self.setLayout(layout_main)
		self.setWindowTitle('%s %s' % (app_name, app_version))
		self.setGeometry(300, 300, 260, 480)
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)	# Always on top!!
		self.show()

	# - Functions --------------------------------
	def mode_changed(self):
		'''The style donor is a live-stroke option only.'''
		self.box_opt.setEnabled(self.rad_live.isChecked())

	def reset_widths(self):
		for master_name, width in master_widths.items():
			self.spn_widths[master_name].setValue(width)

	def donor_set(self):
		glyph = eGlyph()
		layer = glyph.layer()

		for shape in reversed(layer.shapes): # Topmost first
			selected = shape.selected or any(node.selected for contour in shape.contours for node in contour.nodes())

			if selected and not len(shape.includesList):
				self.donor = shape.cloneTopLevel() # A copy: the donor may be edited or removed later
				self.lbl_donor.setText('Donor: {} @ {} (pen {:g}u)'.format(glyph.name, layer.name, shape.pen.widthF()))
				output(0, app_name, 'Style donor set from glyph: {}; Layer: {}.'.format(glyph.name, layer.name))
				return

		output(1, app_name, 'No donor: select a stroked element (not a group) in the active glyph.')

	def donor_clear(self):
		self.donor = None
		self.lbl_donor.setText('Donor: none')

	def current_widths(self, with_filled):
		layer_widths = OrderedDict((master_name, spn.value) for master_name, spn in self.spn_widths.items())

		if with_filled:
			for master_name, width in list(layer_widths.items()):
				layer_widths[master_name + filled_suffix] = width

		return layer_widths

	def action_stroke(self, preset_name):
		preset = presets[preset_name]
		font = pFont()
		process_glyphs = font.selectedGlyphs(extend=eGlyph)

		if not len(process_glyphs):
			active = eGlyph()
			process_glyphs = [active] if active is not None else []

		if not len(process_glyphs):
			output(1, app_name, 'Nothing to stroke! Select glyph(s) or open a glyph in the Glyph window.')
			return

		layer_widths = self.current_widths(preset['filled'])
		live_mode = self.rad_live.isChecked()
		mode_name = 'Live' if live_mode else 'Static'

		for glyph in process_glyphs:
			if live_mode:
				report = stroke_glyph(glyph, layer_widths, preset['cap'], preset['join'], self.donor)
			else:
				report = expand_glyph(glyph, layer_widths, preset['cap_static'], preset['join_static'])

			if len(report): print('{}:\t{}'.format(glyph.name, '; '.join(report)))

		# - Commit
		if len(process_glyphs) > 1:
			font.updateObject(font.fl, '%s | %s | %s; glyphs: %s' % (app_name, mode_name, preset_name, len(process_glyphs)))
		else:
			process_glyphs[0].updateObject(process_glyphs[0].fl, '%s | %s | %s' % (app_name, mode_name, preset_name), verbose=False)

		donor_state = ('yes' if self.donor is not None else 'no') if live_mode else 'n/a'
		output(0, app_name, '%s | %s; Donor: %s; Glyphs: %s' % (mode_name, preset_name, donor_state, len(process_glyphs)))

# - RUN ------------------------------
dialog = dlg_stroke_live()
